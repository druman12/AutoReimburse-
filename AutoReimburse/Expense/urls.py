from django.urls import path
from . import views

urlpatterns = [
    path('add-expense/', views.add_expense, name='add_expense'),
    path('extract-ml/<int:expense_id>/', views.extract_from_expense_document, name='extract_ml'),
    path('api/expense/', views.expense_api, name='create_or_list_expense'),            # POST or GET (all)
    path('api/expense/<int:expense_id>/', views.expense_api, name='get_or_update_expense'),  # GET (by ID) or PUT
]