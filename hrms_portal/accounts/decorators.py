# accounts/decorators.py
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages

def hr_required(view_func):
    """Custom decorator that permits access only to users with is_hr=True."""
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_hr:
            return view_func(request, *args, **kwargs)
        
        # If the user is an employee trying to access HR, kick them back to their workspace
        messages.error(request, "Access Denied. You do not have HR administrative clear level permissions.")
        return redirect('employee_dashboard')
    return _wrapped_view

def employee_required(view_func):
    """Custom decorator that permits access only to regular staff members (is_hr=False)."""
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_hr:
            return view_func(request, *args, **kwargs)
            
        # If HR tries to open an employee profile page, route them back to the admin hub
        return redirect('hr_dashboard')
    return _wrapped_view