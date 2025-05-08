from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User, Department, HR, Employee, Client, Project
import json
import bcrypt


def parse_request_body(request):
    try:
        return json.loads(request.body)
    except Exception:
        return {}


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
def user_api(request, user_id=None):
    if request.method == 'GET':
        if user_id:
            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            data = {
                'username': user.username,
                'email': user.email,
                'phone_number': user.phone_number,
                'user_type': user.user_type,
            }
            return JsonResponse(data)
        else:
            users = list(User.objects.all().values())
            return JsonResponse(users, safe=False)

    
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'error': 'Username and password required'}, status=400)

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

            if user.password_hash == password:
                return JsonResponse({
                    'user_id': user.id,
                    'user_type': user.user_type
                }, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)

@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
def department_api(request, dept_id=None):
    if request.method == 'GET':
        if dept_id:
            dept = Department.objects.filter(id=dept_id).first()
            if not dept:
                return JsonResponse({'error': 'Department not found'}, status=404)
            return JsonResponse({'id': dept.id, 'department_name': dept.department_name, 'description': dept.description})
        else:
            return JsonResponse(list(Department.objects.values()), safe=False)

    


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
def client_api(request, client_id=None):
    if request.method == 'GET':
        if client_id:
            client = Client.objects.filter(id=client_id).first()
            if not client:
                return JsonResponse({'error': 'Client not found'}, status=404)
            data = {
                'id': client.id,
                'client_name': client.client_name,
                'contact_person': client.contact_person,
                'email': client.email,
                'phone_number': client.phone_number,
                'address': client.address,
            }
            return JsonResponse(data, status=200)
        else:
            clients = Client.objects.all().values()
            return JsonResponse(list(clients), safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            client = Client.objects.create(
                client_name=data.get('client_name'),
                contact_person=data.get('contact_person'),
                email=data.get('email'),
                phone_number=data.get('phone_number'),
                address=data.get('address'),
                is_active=data.get('is_active', True)
            )
            return JsonResponse({'message': 'Client created', 'client_id': client.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    

    elif request.method == 'DELETE':
        if not client_id:
            return JsonResponse({'error': 'Client ID required'}, status=400)

        client = Client.objects.filter(id=client_id).first()
        if not client:
            return JsonResponse({'error': 'Client not found'}, status=404)

        client.delete()
        return JsonResponse({'message': 'Client deleted successfully'}, status=200)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def project_list_create(request):
    if request.method == 'GET':
        projects = Project.objects.all().values(
            'id', 'project_name', 'description', 'start_date', 'end_date', 'budget', 'is_active', 'client_id'
        )
        return JsonResponse(list(projects), safe=False, status=200)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            client = Client.objects.filter(id=data.get('client_id')).first() if data.get('client_id') else None
            project = Project.objects.create(
                client=client,
                project_name=data.get('project_name', ''),
                description=data.get('description', ''),
                start_date=parse_date(data.get('start_date')),
                end_date=parse_date(data.get('end_date')),
                budget=data.get('budget'),
                is_active=data.get('is_active', True)
            )
            return JsonResponse({'message': 'Project created', 'id': project.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def project_detail(request, project_id):
    project = Project.objects.filter(id=project_id).first()
    if not project:
        return JsonResponse({'error': 'Project not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'id': project.id,
            'project_name': project.project_name,
            'description': project.description,
            'start_date': project.start_date,
            'end_date': project.end_date,
            'budget': project.budget,
            'is_active': project.is_active,
            'client_id': project.client.id if project.client else None
        }, status=200)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            if 'client_id' in data:
                project.client = Client.objects.filter(id=data.get('client_id')).first()
            project.project_name = data.get('project_name', project.project_name)
            project.description = data.get('description', project.description)
            if data.get('start_date'):
                project.start_date = parse_date(data.get('start_date'))
            if data.get('end_date'):
                project.end_date = parse_date(data.get('end_date'))
            if 'budget' in data:
                project.budget = data.get('budget')
            if 'is_active' in data:
                project.is_active = data.get('is_active')
            project.save()
            return JsonResponse({'message': 'Project updated'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == 'DELETE':
        project.delete()
        return JsonResponse({'message': 'Project deleted'}, status=200)
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Employee, Project, EmployeeProject
import json
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
import datetime

# Helper functions
def parse_date(date_str):
    """Convert date string to datetime object if not None"""
    if date_str:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    return None

# -------------------------- Employee APIs --------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
def employee_list(request):
    """List all employees or create a new employee"""
    if request.method == 'GET':
        employees = Employee.objects.all()
        employee_list = []
        
        for employee in employees:
            employee_data = model_to_dict(employee)
            # Add the username from related User model
            employee_data['username'] = employee.user.username
            # Add projects associated with this employee
            employee_data['projects'] = [
                {
                    'project_id': assignment.project.id,
                    'project_name': assignment.project.project_name,
                    'role': assignment.role,
                    'is_active': assignment.is_active,
                    'assigned_date': assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
                }
                for assignment in employee.project_assignments.all()
            ]
            employee_list.append(employee_data)
            
        return JsonResponse({'employees': employee_list})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            employee = Employee.objects.create(
                user_id=data.get('user_id'),
                hr_id=data.get('hr_id'),
                department_id=data.get('department_id'),
                employee_code=data.get('employee_code'),
                designation=data.get('designation'),
                joining_date=parse_date(data.get('joining_date'))
            )
            return JsonResponse({
                'success': True,
                'message': 'Employee created successfully',
                'employee': model_to_dict(employee)
            }, status=201)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def employee_detail(request, employee_id):
    """Retrieve, update or delete an employee"""
    try:
        employee = Employee.objects.get(id=employee_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Employee not found'
        }, status=404)
    
    if request.method == 'GET':
        employee_data = model_to_dict(employee)
        # Add the username from related User model
        employee_data['username'] = employee.user.username
        # Add projects associated with this employee
        employee_data['projects'] = [
            {
                'project_id': assignment.project.id,
                'project_name': assignment.project.project_name,
                'role': assignment.role,
                'is_active': assignment.is_active,
                'assigned_date': assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
            }
            for assignment in employee.project_assignments.all()
        ]
        return JsonResponse(employee_data)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            # Update fields if provided
            if 'user_id' in data:
                employee.user_id = data['user_id']
            if 'hr_id' in data:
                employee.hr_id = data['hr_id']
            if 'department_id' in data:
                employee.department_id = data['department_id']
            if 'employee_code' in data:
                employee.employee_code = data['employee_code']
            if 'designation' in data:
                employee.designation = data['designation']
            if 'joining_date' in data:
                employee.joining_date = parse_date(data['joining_date'])
            
            employee.save()
            return JsonResponse({
                'success': True,
                'message': 'Employee updated successfully',
                'employee': model_to_dict(employee)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    elif request.method == 'DELETE':
        employee.delete()
        return JsonResponse({
            'success': True,
            'message': 'Employee deleted successfully'
        })

# -------------------------- Project APIs --------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
def project_list(request):
    """List all projects or create a new project"""
    if request.method == 'GET':
        projects = Project.objects.all()
        project_list = []
        
        for project in projects:
            project_data = model_to_dict(project)
            # Add employees associated with this project
            project_data['employees'] = [
                {
                    'employee_id': assignment.employee.id,
                    'employee_name': assignment.employee.user.username,
                    'role': assignment.role,
                    'is_active': assignment.is_active,
                    'assigned_date': assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
                }
                for assignment in project.employee_assignments.all()
            ]
            project_list.append(project_data)
            
        return JsonResponse({'projects': project_list})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            project = Project.objects.create(
                client_id=data.get('client_id'),
                project_name=data.get('project_name'),
                description=data.get('description'),
                start_date=parse_date(data.get('start_date')),
                end_date=parse_date(data.get('end_date')),
                budget=data.get('budget'),
                is_active=data.get('is_active', True)
            )
            return JsonResponse({
                'success': True,
                'message': 'Project created successfully',
                'project': model_to_dict(project)
            }, status=201)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def project_detail(request, project_id):
    """Retrieve, update or delete a project"""
    try:
        project = Project.objects.get(id=project_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Project not found'
        }, status=404)
    
    if request.method == 'GET':
        project_data = model_to_dict(project)
        # Add employees associated with this project
        project_data['employees'] = [
            {
                'employee_id': assignment.employee.id,
                'employee_name': assignment.employee.user.username,
                'role': assignment.role,
                'is_active': assignment.is_active,
                'assigned_date': assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
            }
            for assignment in project.employee_assignments.all()
        ]
        return JsonResponse(project_data)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            # Update fields if provided
            if 'client_id' in data:
                project.client_id = data['client_id']
            if 'project_name' in data:
                project.project_name = data['project_name']
            if 'description' in data:
                project.description = data['description']
            if 'start_date' in data:
                project.start_date = parse_date(data['start_date'])
            if 'end_date' in data:
                project.end_date = parse_date(data['end_date'])
            if 'budget' in data:
                project.budget = data['budget']
            if 'is_active' in data:
                project.is_active = data['is_active']
            
            project.save()
            return JsonResponse({
                'success': True,
                'message': 'Project updated successfully',
                'project': model_to_dict(project)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    elif request.method == 'DELETE':
        project.delete()
        return JsonResponse({
            'success': True,
            'message': 'Project deleted successfully'
        })

# -------------------------- Employee-Project Assignment APIs --------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
def employee_project_list(request):
    """List all employee-project assignments or create a new assignment"""
    if request.method == 'GET':
        assignments = EmployeeProject.objects.all()
        assignment_list = []
        
        for assignment in assignments:
            assignment_data = model_to_dict(assignment)
            assignment_data['employee_name'] = assignment.employee.user.username
            assignment_data['project_name'] = assignment.project.project_name
            assignment_data['assigned_date'] = assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
            assignment_list.append(assignment_data)
            
        return JsonResponse({'assignments': assignment_list})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            employee = Employee.objects.get(id=data.get('employee_id'))
            project = Project.objects.get(id=data.get('project_id'))
            
            # Check if assignment already exists
            if EmployeeProject.objects.filter(employee=employee, project=project).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'This employee is already assigned to this project'
                }, status=400)
            
            assignment = EmployeeProject.objects.create(
                employee=employee,
                project=project,
                role=data.get('role'),
                is_active=data.get('is_active', True)
            )
            
            assignment_data = model_to_dict(assignment)
            assignment_data['employee_name'] = employee.user.username
            assignment_data['project_name'] = project.project_name
            assignment_data['assigned_date'] = assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
            
            return JsonResponse({
                'success': True,
                'message': 'Employee assigned to project successfully',
                'assignment': assignment_data
            }, status=201)
            
        except ObjectDoesNotExist as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def employee_project_detail(request, assignment_id):
    """Retrieve, update or delete an employee-project assignment"""
    try:
        assignment = EmployeeProject.objects.get(id=assignment_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Assignment not found'
        }, status=404)
    
    if request.method == 'GET':
        assignment_data = model_to_dict(assignment)
        assignment_data['employee_name'] = assignment.employee.user.username
        assignment_data['project_name'] = assignment.project.project_name
        assignment_data['assigned_date'] = assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
        return JsonResponse(assignment_data)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            # Update fields if provided
            if 'role' in data:
                assignment.role = data['role']
            if 'is_active' in data:
                assignment.is_active = data['is_active']
                
            # If changing employee or project, check for uniqueness constraint
            if 'employee_id' in data or 'project_id' in data:
                employee_id = data.get('employee_id', assignment.employee_id)
                project_id = data.get('project_id', assignment.project_id)
                
                # Check if this combination would be a duplicate
                if EmployeeProject.objects.filter(
                    employee_id=employee_id, 
                    project_id=project_id
                ).exclude(id=assignment_id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'This employee is already assigned to this project'
                    }, status=400)
                    
                if 'employee_id' in data:
                    assignment.employee_id = employee_id
                if 'project_id' in data:
                    assignment.project_id = project_id
            
            assignment.save()
            
            assignment_data = model_to_dict(assignment)
            assignment_data['employee_name'] = assignment.employee.user.username
            assignment_data['project_name'] = assignment.project.project_name
            assignment_data['assigned_date'] = assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
            
            return JsonResponse({
                'success': True,
                'message': 'Assignment updated successfully',
                'assignment': assignment_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    elif request.method == 'DELETE':
        assignment.delete()
        return JsonResponse({
            'success': True,
            'message': 'Assignment deleted successfully'
        })

# -------------------------- Additional APIs --------------------------

@csrf_exempt
@require_http_methods(["GET", "POST"])
def employee_projects(request, employee_id):
    """Get all projects for a specific employee or assign to multiple projects"""
    try:
        employee = Employee.objects.get(id=employee_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Employee not found'
        }, status=404)
    
    if request.method == 'GET':
        # Get all projects for this employee
        assignments = employee.project_assignments.all()
        projects_data = []
        
        for assignment in assignments:
            project_data = model_to_dict(assignment.project)
            project_data['role'] = assignment.role
            project_data['is_active'] = assignment.is_active
            project_data['assigned_date'] = assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
            projects_data.append(project_data)
            
        return JsonResponse({'projects': projects_data})
    
    elif request.method == 'POST':
        # Add employee to multiple projects
        try:
            data = json.loads(request.body)
            project_ids = data.get('project_ids', [])
            role = data.get('role', '')
            is_active = data.get('is_active', True)
            
            added_projects = []
            for project_id in project_ids:
                try:
                    project = Project.objects.get(id=project_id)
                    # Check if relationship already exists
                    if not EmployeeProject.objects.filter(employee=employee, project=project).exists():
                        assignment = EmployeeProject.objects.create(
                            employee=employee,
                            project=project,
                            role=role,
                            is_active=is_active
                        )
                        added_projects.append({
                            'id': project.id,
                            'name': project.project_name,
                            'assignment_id': assignment.id
                        })
                except ObjectDoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Added employee to {len(added_projects)} projects',
                'added_projects': added_projects
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def project_employees(request, project_id):
    """Get all employees for a specific project or assign multiple employees"""
    try:
        project = Project.objects.get(id=project_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Project not found'
        }, status=404)
    
    if request.method == 'GET':
        # Get all employees for this project
        assignments = project.employee_assignments.all()
        employees_data = []
        
        for assignment in assignments:
            employee_data = model_to_dict(assignment.employee)
            employee_data['username'] = assignment.employee.user.username
            employee_data['role'] = assignment.role
            employee_data['is_active'] = assignment.is_active
            employee_data['assigned_date'] = assignment.assigned_date.strftime('%Y-%m-%d') if assignment.assigned_date else None
            employees_data.append(employee_data)
            
        return JsonResponse({'employees': employees_data})
    
    elif request.method == 'POST':
        # Add multiple employees to this project
        try:
            data = json.loads(request.body)
            employee_ids = data.get('employee_ids', [])
            role = data.get('role', '')
            is_active = data.get('is_active', True)
            
            added_employees = []
            for employee_id in employee_ids:
                try:
                    employee = Employee.objects.get(id=employee_id)
                    # Check if relationship already exists
                    if not EmployeeProject.objects.filter(employee=employee, project=project).exists():
                        assignment = EmployeeProject.objects.create(
                            employee=employee,
                            project=project,
                            role=role,
                            is_active=is_active
                        )
                        added_employees.append({
                            'id': employee.id,
                            'name': employee.user.username,
                            'assignment_id': assignment.id
                        })
                except ObjectDoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Added {len(added_employees)} employees to project',
                'added_employees': added_employees
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def remove_employee_from_project(request, project_id, employee_id):
    """Remove a specific employee from a specific project"""
    try:
        # Check if both project and employee exist
        project = Project.objects.get(id=project_id)
        employee = Employee.objects.get(id=employee_id)
        
        # Find and delete the assignment if it exists
        try:
            assignment = EmployeeProject.objects.get(employee=employee, project=project)
            assignment.delete()
            return JsonResponse({
                'success': True,
                'message': 'Employee removed from project successfully'
            })
        except ObjectDoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'This employee is not assigned to this project'
            }, status=404)
            
    except ObjectDoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Project or Employee not found'
        }, status=404)