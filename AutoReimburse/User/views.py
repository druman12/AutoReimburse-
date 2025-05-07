from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import User, Department, HR, Employee, Client, Project
import json


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
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'user_type': user.user_type,
                'is_active': user.is_active,
            }
            return JsonResponse(data)
        else:
            users = list(User.objects.all().values())
            return JsonResponse(users, safe=False)

    elif request.method == 'POST':
        data = parse_request_body(request)
        user = User.objects.create(
            username=data.get('username'),
            password_hash=data.get('password_hash'),
            email=data.get('email'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone_number=data.get('phone_number'),
            user_type=data.get('user_type'),
        )
        return JsonResponse({'message': 'User created', 'user_id': user.id}, status=201)

    elif request.method == 'PUT':
        if not user_id:
            return JsonResponse({'error': 'User ID required'}, status=400)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)

        data = parse_request_body(request)
        user.username = data.get('username', user.username)
        user.password_hash = data.get('password_hash', user.password_hash)
        user.email = data.get('email', user.email)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone_number = data.get('phone_number', user.phone_number)
        user.user_type = data.get('user_type', user.user_type)
        user.is_active = data.get('is_active', user.is_active)
        user.save()
        return JsonResponse({'message': 'User updated successfully'})

    elif request.method == 'DELETE':
        if not user_id:
            return JsonResponse({'error': 'User ID required'}, status=400)
        user = User.objects.filter(id=user_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)
        user.delete()
        return JsonResponse({'message': 'User deleted successfully'})


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

    elif request.method == 'POST':
        data = parse_request_body(request)
        dept = Department.objects.create(
            department_name=data.get('department_name'),
            description=data.get('description')
        )
        return JsonResponse({'message': 'Department created', 'id': dept.id}, status=201)

    elif request.method == 'PUT':
        if not dept_id:
            return JsonResponse({'error': 'Department ID required'}, status=400)
        dept = Department.objects.filter(id=dept_id).first()
        if not dept:
            return JsonResponse({'error': 'Department not found'}, status=404)
        data = parse_request_body(request)
        dept.department_name = data.get('department_name', dept.department_name)
        dept.description = data.get('description', dept.description)
        dept.save()
        return JsonResponse({'message': 'Department updated'})

    elif request.method == 'DELETE':
        if not dept_id:
            return JsonResponse({'error': 'Department ID required'}, status=400)
        dept = Department.objects.filter(id=dept_id).first()
        if not dept:
            return JsonResponse({'error': 'Department not found'}, status=404)
        dept.delete()
        return JsonResponse({'message': 'Department deleted'})


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
                'is_active': client.is_active,
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

    elif request.method == 'PUT':
        if not client_id:
            return JsonResponse({'error': 'Client ID required'}, status=400)

        client = Client.objects.filter(id=client_id).first()
        if not client:
            return JsonResponse({'error': 'Client not found'}, status=404)

        try:
            data = json.loads(request.body)
            client.client_name = data.get('client_name', client.client_name)
            client.contact_person = data.get('contact_person', client.contact_person)
            client.email = data.get('email', client.email)
            client.phone_number = data.get('phone_number', client.phone_number)
            client.address = data.get('address', client.address)
            client.is_active = data.get('is_active', client.is_active)
            client.save()
            return JsonResponse({'message': 'Client updated successfully'}, status=200)
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
