from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
# Register your models here.

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('HRMS Roles', { 'fields': ('is_hr','is_employee')}),
    )

admin.site.register(User, CustomUserAdmin)

