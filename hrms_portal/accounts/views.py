from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count

import json
from employees.models import EmployeeProfile, Department
from leaves.models import LeaveRequest
from leaves.forms import LeaveApplicationForm


# Create your views here.
@login_required
def dashboard_router(request):
    """ 
    acts as traffic controller. instpect user role and redirect to their designated dash work space.
    """ 
    user = request.user
    if user.is_hr:
        return redirect('hr_dashboard')
    elif user.is_employee:
        return redirect('employee_dashboard')
    else:
        return render(request, 'accounts/no_role.html')

# accounts/views.py (Inside your hr_dashboard function)

@login_required
def hr_dashboard(request):
    if not request.user.is_hr:
        return redirect('dashboard_home')
        
    # 1. Gather global metrics counters
    total_staff = EmployeeProfile.objects.count() or 0
    pending_leaves = LeaveRequest.objects.filter(status='PENDING').count() or 0
    
    salary_dict = EmployeeProfile.objects.aggregate(Sum('salary'))
    raw_payroll = salary_dict.get('salary__sum') or 0.00
    total_payroll = float(raw_payroll)

    # 2. Fetch all leave requests (Pending first, then newest)
    recent_requests = LeaveRequest.objects.select_related('user').all().order_by('status', '-applied_on')[:10]
    
    # 3. Process chart variables
    department_counts = Department.objects.annotate(total_employees=Count('employees'))
    if not department_counts.exists():
        chart_labels = json.dumps(["No Active Departments"])
        chart_data = json.dumps([1])
    else:
        chart_labels = json.dumps([dept.name for dept in department_counts])
        chart_data = json.dumps([dept.total_employees for dept in department_counts])

    context = {
        'total_staff': total_staff,
        'pending_leaves': pending_leaves,
        'total_payroll': total_payroll,
        'recent_requests': recent_requests, # <-- Crucial context list
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'accounts/hr_dashboard.html', context)


@login_required
def employee_dashboard(request):
    if not request.user.is_employee:
        return redirect('dashboard_home') 

    profile = EmployeeProfile.objects.filter(user=request.user).select_related('department').first()
    
    # --- FIXED TYPO: Changed .order_selection to proper .order_by ---
    my_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-applied_on')[:5]
    
    # statistics
    approved_count = LeaveRequest.objects.filter(user=request.user, status='APPROVED').count()
    pending_count = LeaveRequest.objects.filter(user=request.user, status='PENDING').count()

    context = {
        'profile': profile,
        'my_leaves': my_leaves,
        'approved_count': approved_count,
        'pending_count': pending_count,
    }

    # --- FIXED BUG: Now explicitly passing the context variables package ---
    return render(request, 'accounts/employee_dashboard.html', context)


@login_required
def apply_leave(request):
    if not request.user.is_employee:
        return redirect('dashboard_home')
    
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST)
        if form.is_valid():
            leave_instance = form.save(commit=False)
            leave_instance.user = request.user
            leave_instance.save()
            return redirect('employee_dashboard')
    else:
        form = LeaveApplicationForm()

    return render(request, 'accounts/apply_leave.html', {'form': form})


@login_required
def approve_leave_action(request, leave_id):
    """Securely flags a targeted leave entry row as APPROVED."""
    if not request.user.is_hr:
        return redirect('dashboard_home')
        
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    leave.status = 'APPROVED'
    leave.save()
    return redirect('hr_dashboard')

@login_required
def reject_leave_action(request, leave_id):
    """Securely flags a targeted leave entry row as REJECTED."""
    if not request.user.is_hr:
        return redirect('dashboard_home')
        
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    leave.status = 'REJECTED'
    leave.save()
    return redirect('hr_dashboard')