from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .expense_prediction_model import ExpensePredictionModel

@csrf_exempt
@require_http_methods(["GET", "POST"])
def expense_predictions(request):
    """
    Endpoint for expense predictions
    GET: Get predictions
    POST: Train models
    """
    if request.method == "POST":
        try:
            # Parse request body
            data = json.loads(request.body)
            action = data.get('action', '')
            
            model = ExpensePredictionModel()
            
            if action == "train_all":
                # Train all models
                monthly_result = model.train_monthly_expense_model()
                budget_result = model.train_budget_overrun_model()
                project_result = model.train_project_expense_model()
                
                return JsonResponse({
                    'status': 'success',
                    'results': {
                        'monthly_expense_model': monthly_result,
                        'budget_overrun_model': budget_result,
                        'project_expense_model': project_result
                    }
                })
                
            elif action == "train_monthly":
                result = model.train_monthly_expense_model()
                return JsonResponse({'status': 'success', 'result': result})
                
            # elif action == "train_budget":
            #     result = model.train_budget_overrun_model()
            #     return JsonResponse({'status': 'success', 'result': result})
                
            elif action == "train_project":
                result = model.train_project_expense_model()
                return JsonResponse({'status': 'success', 'result': result})
                
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    else:  # GET request
        try:
            # Parse query parameters
            prediction_type = request.GET.get('type', 'all')
            project_id = request.GET.get('project_id')
            
            model = ExpensePredictionModel()
            results = {}
            
            if prediction_type in ['all', 'monthly']:
                results['monthly_expense'] = model.predict_next_month_expense()
                
            if prediction_type in ['all', 'budget']:
                results['budget_overruns'] = model.predict_budget_overruns()
                
            if prediction_type in ['all', 'project']:
                if project_id:
                    results['project_expenses'] = model.predict_project_expenses(project_id=project_id)
                else:
                    results['project_expenses'] = model.predict_project_expenses()
            
            return JsonResponse({
                'status': 'success',
                'predictions': results
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def expense_insights(request):
    """
    Provide business insights based on expense data and predictions
    """
    try:
        model = ExpensePredictionModel()
        
        # Get predictions
        monthly_prediction = model.predict_next_month_expense()
        budget_predictions = model.predict_budget_overruns()
        project_predictions = model.predict_project_expenses()
        
        # Calculate insights
        insights = []
        
        # Monthly expense trend insight
        if monthly_prediction.get('status') == 'success':
            prediction = float(monthly_prediction.get('prediction', 0))
            
            # Get current month's expenses
            from django.db.models import Sum
            from django.db.models.functions import TruncMonth
            from .models import Expense
            import datetime
            from decimal import Decimal
            
            current_month = datetime.datetime.now().replace(day=1)
            current_expenses_decimal = Expense.objects.filter(
                expense_date__year=current_month.year,
                expense_date__month=current_month.month
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            # Convert Decimal to float for calculations
            current_expenses = float(current_expenses_decimal)
            
            # Calculate percentage change
            if current_expenses > 0:
                percent_change = ((prediction - current_expenses) / current_expenses) * 100
                trend = "increase" if percent_change > 0 else "decrease"
                
                insights.append({
                    'type': 'monthly_trend',
                    'title': f"Expected {abs(round(percent_change, 1))}% {trend} in expenses next month",
                    'description': f"Next month's expenses are predicted to be ${prediction:.2f}, compared to ${current_expenses:.2f} this month.",
                    'severity': 'warning' if percent_change > 10 else 'info'
                })
        
        # Budget risk insights
        if budget_predictions.get('status') == 'success':
            high_risk_categories = [
                item for item in budget_predictions.get('predictions', [])
                if item['risk_level'] == 'High'
            ]
            
            if high_risk_categories:
                insights.append({
                    'type': 'budget_risk',
                    'title': f"{len(high_risk_categories)} categories at high risk of budget overrun",
                    'description': f"Categories at risk: {', '.join(item['category_name'] for item in high_risk_categories[:3])}{'...' if len(high_risk_categories) > 3 else ''}",
                    'severity': 'warning',
                    'affected_categories': [item['category_id'] for item in high_risk_categories]
                })
        
        # Project expense insights
        if project_predictions.get('status') == 'success':
            over_budget_projects = [
                item for item in project_predictions.get('predictions', [])
                if float(item['remaining_budget']) < 0
            ]
            
            if over_budget_projects:
                insights.append({
                    'type': 'project_budget',
                    'title': f"{len(over_budget_projects)} projects predicted to exceed budget",
                    'description': f"Projects at risk: {', '.join(item['project_name'] for item in over_budget_projects[:3])}{'...' if len(over_budget_projects) > 3 else ''}",
                    'severity': 'danger',
                    'affected_projects': [item['project_id'] for item in over_budget_projects]
                })
            
            # Find projects with significant remaining budget
            efficient_projects = [
                item for item in project_predictions.get('predictions', [])
                if float(item['current_expenses']) > 0 and float(item['remaining_budget']) > 0.5 * float(item['current_expenses'])
            ]
            
            if efficient_projects:
                insights.append({
                    'type': 'budget_efficiency',
                    'title': f"{len(efficient_projects)} projects running under budget",
                    'description': f"Projects with significant budget remaining: {', '.join(item['project_name'] for item in efficient_projects[:3])}{'...' if len(efficient_projects) > 3 else ''}",
                    'severity': 'success',
                    'affected_projects': [item['project_id'] for item in efficient_projects]
                })
        
        return JsonResponse({
            'status': 'success',
            'insights': insights,
            'predictions': {
                'monthly': monthly_prediction if monthly_prediction.get('status') == 'success' else None,
                'budget': budget_predictions if budget_predictions.get('status') == 'success' else None,
                'project': project_predictions if project_predictions.get('status') == 'success' else None
            }
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)