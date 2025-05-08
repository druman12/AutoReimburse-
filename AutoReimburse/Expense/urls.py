from django.urls import path
from . import views , expense_prediction_view

urlpatterns = [
    path('add-expense/', views.add_expense, name='add_expense'),
    path('extract-ml/<int:expense_id>/', views.extract_from_expense_document, name='extract_ml'),
    path('api/expense/', views.expense_api, name='create_or_list_expense'),            # POST or GET (all)
    path('api/expense/<int:expense_id>/', views.expense_api, name='get_or_update_expense'),  # GET (by ID) or PUT
    path('api/expense-statistics/', views.expense_statistics, name='expense-statistics'),
    path('api/expense-predictions/', expense_prediction_view.expense_predictions, name='expense-predictions'),
    path('api/expense-insights/', expense_prediction_view.expense_insights, name='expense-insights'),

]