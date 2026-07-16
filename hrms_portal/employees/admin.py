from django.contrib import admin
from .models import Department, EmployeeProfile
# Register your models here.

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name','code')
    search_fields = ('name','code')

class EmplyeeProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'designation', 'joining_date', 'salary')
    list_filter = ('department', 'gender')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name', 'designation')