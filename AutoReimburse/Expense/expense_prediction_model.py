import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from datetime import datetime, timedelta
import os
import warnings

from django.conf import settings
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth

from .models import Expense, ExpenseCategory, Project, Employee


class ExpensePredictionModel:
    """
    A class to build ML models for expense-related predictions adapted for small datasets
    """
    
    def __init__(self):
        self.model_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Model file paths
        self.monthly_expense_model_path = os.path.join(self.model_dir, 'monthly_expense_predictor.joblib')
        self.budget_overrun_model_path = os.path.join(self.model_dir, 'budget_overrun_predictor.joblib')
        self.project_expense_model_path = os.path.join(self.model_dir, 'project_expense_predictor.joblib')
        
        # Minimum data requirements
        self.min_records = 3  # Absolute minimum needed
        
    def _prepare_monthly_expense_data(self):
        """Prepare data for monthly expense prediction - improved for small datasets"""
        # Get expenses grouped by month
        expenses = Expense.objects.annotate(
            month=TruncMonth('expense_date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        # Convert to pandas dataframe
        expenses_list = list(expenses)
        
        # Convert Decimal to float for all numeric values
        for item in expenses_list:
            if 'total' in item and item['total'] is not None:
                item['total'] = float(item['total'])
            if 'count' in item and item['count'] is not None:
                item['count'] = float(item['count'])
        
        df = pd.DataFrame(expenses_list)
        
        if df.empty or len(df) < self.min_records:
            return None, None
        
        # Check for and handle extreme outliers
        q1 = df['total'].quantile(0.25)
        q3 = df['total'].quantile(0.75)
        iqr = q3 - q1
        upper_bound = q3 + 1.5 * iqr
        lower_bound = q1 - 1.5 * iqr
        
        # Log outlier information but don't remove with small data
        outliers = df[(df['total'] > upper_bound) | (df['total'] < lower_bound)]
        if not outliers.empty:
            print(f"Warning: {len(outliers)} outliers detected in expense data")
        
        # Features for small data
        df['month_num'] = df['month'].apply(lambda x: x.month)
        
        # Add quarter information (seasonal pattern)
        df['quarter'] = df['month'].apply(lambda x: (x.month - 1) // 3 + 1)
        
        # Add previous month's total with better handling
        df['prev_total'] = df['total'].shift(1)
        # For the first record, use a reasonable estimate instead of mean
        if len(df) > 1:
            df.loc[df['prev_total'].isnull(), 'prev_total'] = df['total'].iloc[1]
        else:
            df.loc[df['prev_total'].isnull(), 'prev_total'] = df['total'].iloc[0] * 0.9
        
        # Feature set
        X = df[['month_num', 'quarter', 'prev_total']]
        y = df['total']
        
        return X, y

    def _prepare_project_expense_data(self):
        """Prepare data for predicting project expenses - simplified for small datasets"""
        # Get project features with expenses
        project_expenses = Expense.objects.filter(
            project__isnull=False
        ).values(
            'project__id', 'project__project_name', 'project__start_date', 'project__end_date'
        ).annotate(
            total_expense=Sum('amount'),
            expense_count=Count('id')
        )
        
        # Convert to list and handle Decimal values
        project_expenses_list = list(project_expenses)
        
        # Convert Decimal to float for all numeric values
        for item in project_expenses_list:
            if 'total_expense' in item and item['total_expense'] is not None:
                item['total_expense'] = float(item['total_expense'])
            if 'expense_count' in item and item['expense_count'] is not None:
                item['expense_count'] = float(item['expense_count'])
        
        df = pd.DataFrame(project_expenses_list)
        
        if df.empty or len(df) < self.min_records:
            return None, None
            
        # Calculate simplified duration feature
        df['duration'] = df.apply(
            lambda row: (row['project__end_date'] - row['project__start_date']).days 
            if row['project__end_date'] else 365, axis=1
        )
        
        # Feature selection - simpler for small datasets
        feature_cols = ['duration', 'expense_count']
        
        # Features and target
        X = df[feature_cols]
        y = df['total_expense']
        
        return X, y
    
    def _prepare_budget_overrun_data(self):
        """Prepare data for budget overrun prediction"""
        # Get category data with budget information
        categories = ExpenseCategory.objects.filter(budget_limit__isnull=False)
        
        if not categories or categories.count() < self.min_records:
            return None, None
            
        data = []
        
        for category in categories:
            # Get historical data for this category
            monthly_expenses = Expense.objects.filter(
                category=category
            ).annotate(
                month=TruncMonth('expense_date')
            ).values('month').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('month')
            
            for month_data in monthly_expenses:
                # Convert Decimal to float
                month_total = float(month_data['total']) if month_data['total'] is not None else 0.0
                budget_limit = float(category.budget_limit) if category.budget_limit is not None else 0.0
                
                # Skip if budget is zero (no meaningful limit)
                if budget_limit <= 0:
                    continue
                    
                # Calculate features
                data.append({
                    'category_id': category.id,
                    'month': month_data['month'],
                    'total': month_total,
                    'count': month_data['count'],
                    'budget': budget_limit,
                    'pct_used': month_total / budget_limit if budget_limit > 0 else 1.0,
                    'overrun': 1 if month_total > budget_limit else 0
                })
        
        if not data or len(data) < self.min_records:
            return None, None
            
        df = pd.DataFrame(data)
        
        # Features and target
        X = df[['total', 'count', 'budget', 'pct_used']]
        y = df['overrun']
        
        return X, y
    
    def train_monthly_expense_model(self):
        """Train model to predict next month's total expenses with small datasets"""
        X, y = self._prepare_monthly_expense_data()
        
        if X is None or y is None:
            return {'status': 'error', 'message': f'Insufficient data for training. Need at least {self.min_records} records.'}
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Scale target (important for large expense values)
        y_mean = float(np.mean(y))
        y_std = float(np.std(y))
        if y_std == 0:  # Avoid division by zero
            y_std = 1.0
        y_scaled = (y - y_mean) / y_std
        
        # For very small datasets, use stronger regularization
        if len(X) <= 10:
            # Increased regularization for very small datasets
            model = Ridge(alpha=50.0)
        else:
            model = Ridge(alpha=10.0)
        
        # Train model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(X_scaled, y_scaled)
        
        # Save model along with scalers for later use
        joblib.dump((model, scaler, y_mean, y_std), self.monthly_expense_model_path)
        
        # Make predictions for evaluation
        y_pred_scaled = model.predict(X_scaled)
        y_pred = y_pred_scaled * y_std + y_mean
        
        # Calculate metrics
        mse = float(mean_squared_error(y, y_pred))
        r2 = float(r2_score(y, y_pred))
        
        return {
            'status': 'success',
            'message': f'Model trained on {len(X)} records',
            'metrics': {
                'mse': mse,
                'r2': r2
            }
        }

    
    def _train_with_loo_cv(self, X, y, model_type='regression'):
        """Train with Leave-One-Out cross validation for very small datasets"""
        loo = LeaveOneOut()
        
        if model_type == 'regression':
            # Ridge regression with regularization for small datasets
            model = Ridge(alpha=5.0)
        else:
            # Logistic regression with regularization for small datasets
            model = LogisticRegression(C=0.1, solver='liblinear')
            
        # Scale data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train with all data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(X_scaled, y)
            
        return model
    
    def train_budget_overrun_model(self):
        """Train model to predict which categories might exceed budget with small datasets"""
        X, y = self._prepare_budget_overrun_data()
        
        if X is None or y is None:
            return {'status': 'error', 'message': f'Insufficient data for training. Need at least {self.min_records} records.'}
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # For very small datasets, use RandomForestClassifier
        model = RandomForestClassifier(n_estimators=100, random_state=42)
            
        # Train model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(X_scaled, y)
        
        # Save model along with scaler
        joblib.dump((model, scaler), self.budget_overrun_model_path)
        y_pred = model.predict_proba(X_scaled)[:, 1]
    
        return {
            'status': 'success',
            'message': f'Model trained on {len(X)} records',
            'metrics': {
                'accuracy': float(model.score(X_scaled, y))
            }
        }


    
    def train_project_expense_model(self):
        """Train model to predict total expenses for projects with small datasets"""
        X, y = self._prepare_project_expense_data()
        
        if X is None or y is None:
            return {'status': 'error', 'message': f'Insufficient data for training. Need at least {self.min_records} records.'}
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Ridge regression with strong regularization for small datasets
        model = Ridge(alpha=10.0)
        
        # Train model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(X_scaled, y)
        
        # Save model along with scaler
        joblib.dump((model, scaler), self.project_expense_model_path)
        
        # Calculate metrics on training data
        y_pred = model.predict(X_scaled)
        mse = float(mean_squared_error(y, y_pred))
        r2 = float(r2_score(y, y_pred))
        
        return {
            'status': 'success',
            'message': f'Model trained on {len(X)} records',
            'metrics': {
                'mse': mse,
                'r2': r2
            }
        }
    
    def predict_next_month_expense(self):
        """Predict next month's total expenses"""
        try:
            # Load model
            if not os.path.exists(self.monthly_expense_model_path):
                return {'status': 'error', 'message': 'Model not trained yet'}
                
            # Unpack model and scalers
            model, scaler, y_mean, y_std = joblib.load(self.monthly_expense_model_path)
            
            # Get latest month data
            latest_expense = Expense.objects.annotate(
                month=TruncMonth('expense_date')
            ).values('month').annotate(
                total=Sum('amount')
            ).order_by('-month').first()
            
            if not latest_expense:
                return {'status': 'error', 'message': 'No historical expense data available'}
            
            # Extract feature values
            now = datetime.now()
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            next_month_num = next_month.month
            next_month_quarter = (next_month_num - 1) // 3 + 1
            
            # Convert Decimal to float
            prev_month_total = float(latest_expense['total']) if latest_expense['total'] is not None else 0.0
            
            # Create input data
            X_pred = pd.DataFrame({
                'month_num': [next_month_num],
                'quarter': [next_month_quarter],
                'prev_total': [prev_month_total]
            })
            
            # Scale input
            X_scaled = scaler.transform(X_pred)
            
            # Make prediction and unscale
            prediction_scaled = model.predict(X_scaled)[0]
            prediction = float(prediction_scaled * y_std + y_mean)
            
            return {
                'status': 'success',
                'prediction': prediction,
                'next_month': next_month.strftime('%B %Y'),
                'note': 'Prediction based on limited data, use with caution'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def predict_budget_overruns(self):
        """Predict which categories might exceed budget next month"""
        try:
            # Load model
            if not os.path.exists(self.budget_overrun_model_path):
                return {'status': 'error', 'message': 'Model not trained yet'}
                
            model, scaler = joblib.load(self.budget_overrun_model_path)
            
            # Get categories
            categories = ExpenseCategory.objects.all()
            results = []
            
            # For each category, predict risk of overrun
            for category in categories:
                # Get current data for category
                cat_total_query = Expense.objects.filter(category=category).aggregate(Sum('amount'))
                cat_total = float(cat_total_query['amount__sum']) if cat_total_query['amount__sum'] is not None else 0.0
                cat_count = Expense.objects.filter(category=category).count()
                budget_limit = float(category.budget_limit) if category.budget_limit is not None else 0.0
                
                # Skip if no budget limit
                if budget_limit <= 0:
                    continue
                
                # Calculate percentage used
                pct_used = cat_total / budget_limit if budget_limit > 0 else 1.0
                
                # Prepare input features
                X_pred = pd.DataFrame({
                    'total': [cat_total],
                    'count': [cat_count],
                    'budget': [budget_limit],
                    'pct_used': [pct_used]
                })
                
                # Scale input
                X_scaled = scaler.transform(X_pred)
                
                # Make prediction
                prediction = float(model.predict_proba(X_scaled)[0][1])
                
                results.append({
                    'category_id': category.id,
                    'category_name': category.category_name,
                    'budget_limit': budget_limit,
                    'current_total': cat_total,
                    'overrun_probability': prediction,
                    'risk_level': 'High' if prediction > 0.7 else 'Medium' if prediction > 0.3 else 'Low',
                    'note': 'Prediction based on limited data'
                })
            
            # Sort by overrun probability (highest first)
            results.sort(key=lambda x: x['overrun_probability'], reverse=True)
            
            now = datetime.now()
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            
            return {
                'status': 'success',
                'predictions': results,
                'next_month': next_month.strftime('%B %Y'),
                'note': 'Predictions based on limited data, use with caution'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def predict_project_expenses(self, project_id=None):
        """Predict total expenses for a project"""
        try:
            # Load model
            if not os.path.exists(self.project_expense_model_path):
                return {'status': 'error', 'message': 'Model not trained yet'}
                
            model, scaler = joblib.load(self.project_expense_model_path)
            
            # Get projects to predict for
            if project_id:
                projects = Project.objects.filter(id=project_id)
            else:
                projects = Project.objects.filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=datetime.now().date())
                )
            
            if not projects:
                return {'status': 'error', 'message': 'No projects found'}
            
            results = []
            
            for project in projects:
                # Get project features
                duration = (project.end_date - project.start_date).days if project.end_date else 365
                
                # Get current expense count
                expense_count = Expense.objects.filter(project=project).count()
                
                # Prepare input features
                X_pred = pd.DataFrame({
                    'duration': [float(duration)],
                    'expense_count': [float(expense_count)]
                })
                
                # Scale input
                X_scaled = scaler.transform(X_pred)
                
                # Make prediction
                prediction = float(model.predict(X_scaled)[0])
                
                # Get current total
                current_total_query = Expense.objects.filter(project=project).aggregate(Sum('amount'))
                current_total = float(current_total_query['amount__sum']) if current_total_query['amount__sum'] is not None else 0.0
                
                results.append({
                    'project_id': project.id,
                    'project_name': project.name,
                    'current_expenses': current_total,
                    'predicted_total': prediction,
                    'remaining_budget': prediction - current_total,
                    'note': 'Prediction based on limited data'
                })
            
            return {
                'status': 'success',
                'predictions': results,
                'note': 'Predictions based on limited data, use with caution'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}