from django.db import models
from django.utils import timezone

class User(models.Model):
    USER_TYPE_CHOICES = [
        ('HR', 'HR'),
        ('Employee', 'Employee'),
    ]

    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} ({self.user_type})"

    @classmethod
    def get_hr_users(cls):
        return cls.objects.filter(user_type='HR')

    @classmethod
    def get_employee_users(cls):
        return cls.objects.filter(user_type='Employee')


class Department(models.Model):
    department_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.department_name

class HR(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'HR'}
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    designation = models.CharField(max_length=100)
    joining_date = models.DateField()

    def __str__(self):
        return f"{self.user.username} - HR"


class Employee(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'Employee'}
    )
    hr = models.ForeignKey(
        HR,
        on_delete=models.CASCADE
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    employee_code = models.CharField(max_length=20, unique=True)
    designation = models.CharField(max_length=100)
    joining_date = models.DateField()
   
    def __str__(self):
        return f"{self.user.username} - Employee"


class Client(models.Model):
    client_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.client_name


class Project(models.Model):
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    project_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.project_name

