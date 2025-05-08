from django.contrib import admin
from .models import User , HR , Employee , Department , Project , Client , EmployeeProject

# Register your models here.
admin.site.register(User)
admin.site.register(HR)
admin.site.register(Employee)
admin.site.register(Department)
admin.site.register(Project)
admin.site.register(Client)
admin.site.register(EmployeeProject)