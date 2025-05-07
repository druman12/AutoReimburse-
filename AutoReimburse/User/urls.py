from django.urls import path
from . import views

urlpatterns = [
    path('api/client/', views.client_api, name='client_create_or_list'),
    path('api/client/<int:client_id>/', views.client_api, name='client_detail_update_delete'),
    path('api/project/', views.project_list_create, name='client_create_or_list'),
    path('api/project/<int:project_id>/', views.project_detail, name='client_detail_update_delete'),
    path('api/department/', views.department_api, name='client_create_or_list'),
    path('api/department/<int:project_id>/', views.department_api, name='client_detail_update_delete'),
]