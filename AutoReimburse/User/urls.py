from django.urls import path
from . import views

urlpatterns = [
    path('api/login/', views.login_view , name="login views"),
    path('api/client/', views.client_api, name='client_create_or_list'),
    path('api/client/<int:client_id>/', views.client_api, name='client_detail_update_delete'),
    path('api/project/', views.project_list_create, name='client_create_or_list'),
    path('api/project/<int:project_id>/', views.project_detail, name='client_detail_update_delete'),
    path('api/department/', views.department_api, name='client_create_or_list'),
    path('api/department/<int:project_id>/', views.department_api, name='client_detail_update_delete'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    
    # Project APIs
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    
    # Employee-Project Assignment APIs
    path('assignments/', views.employee_project_list, name='employee_project_list'),
    path('assignments/<int:assignment_id>/', views.employee_project_detail, name='employee_project_detail'),
    
    # Additional APIs for direct management of relationships
    path('employees/<int:employee_id>/projects/', views.employee_projects, name='employee_projects'),
    path('projects/<int:project_id>/employees/', views.project_employees, name='project_employees'),
    path('projects/<int:project_id>/employees/<int:employee_id>/', views.remove_employee_from_project, name='remove_employee_from_project'),
]