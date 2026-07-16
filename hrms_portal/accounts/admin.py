from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, EmployeeProfile

# Register your models here.

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('HRMS Roles', { 'fields': ('is_hr','is_employee')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(EmployeeProfile)
