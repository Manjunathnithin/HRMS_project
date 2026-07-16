import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count

from employees.models import EmployeeProfile, Department
from leaves.models import LeaveRequest, LeaveBalance
from leaves.forms import LeaveApplicationForm

@login_required
def dashboard_router(request):
    user = request.user
    if user.is_hr:
        return redirect('hr_dashboard')
    elif user.is_employee:
        return redirect('employee_dashboard')
    else:
        return render(request, 'accounts/no_role.html')

@login_required
def hr_dashboard(request):
    if not request.user.is_hr:
        return redirect('dashboard_home')
        
    total_staff = EmployeeProfile.objects.count() or 0
    # FIXED: Changed 'PENDING' to 'Pending'
    pending_leaves = LeaveRequest.objects.filter(status='Pending').count() or 0
    
    salary_dict = EmployeeProfile.objects.aggregate(Sum('salary'))
    raw_payroll = salary_dict.get('salary__sum') or 0.00
    total_payroll = float(raw_payroll)

    recent_requests = LeaveRequest.objects.select_related('user').all().order_by('status', '-applied_on')[:10]

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
        'recent_requests': recent_requests,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'accounts/hr_dashboard.html', context)

# accounts/views.py
@login_required
def employee_dashboard(request):
    if not request.user.is_employee:
        return redirect('dashboard_home') 

    profile = EmployeeProfile.objects.filter(user=request.user).select_related('department').first()
    my_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-applied_on')[:5]
    
    balances, created = LeaveBalance.objects.get_or_create(user=request.user)
    
    approved_count = LeaveRequest.objects.filter(user=request.user, status='Approved').count()
    pending_count = LeaveRequest.objects.filter(user=request.user, status='Pending').count()

    context = {
        'profile': profile,
        'my_leaves': my_leaves,
        'balances': balances,
        'approved_count': approved_count,
        'pending_count': pending_count,
    }
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
    """Securely flags a targeted leave entry row as Approved and deducts quota days."""
    if not request.user.is_hr:
        return redirect('dashboard_home')
        
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    
    # Process deduction only if it isn't already processed (avoids double deduction)
    if leave.status == 'Pending':
        leave.status = 'Approved'
        leave.save()
        
        # 1. Dynamically compute the duration in days (+1 makes it inclusive)
        if leave.start_date and leave.end_date:
            duration_days = (leave.end_date - leave.start_date).days + 1
            
            # 2. Grab or generate the employee's allocation card row
            balance, created = LeaveBalance.objects.get_or_create(user=leave.user)
            
            # 3. Deduct from the matching code configuration type
            if leave.leave_type == 'SL':
                balance.sick_leave_remaining = max(0, balance.sick_leave_remaining - duration_days)
            elif leave.leave_type == 'PL':
                balance.personal_leave_remaining = max(0, balance.personal_leave_remaining - duration_days)
            elif leave.leave_type == 'CL':
                balance.casual_leave_remaining = max(0, balance.casual_leave_remaining - duration_days)
                
            balance.save()
            
    return redirect('hr_dashboard')

@login_required
def reject_leave_action(request, leave_id):
    if not request.user.is_hr:
        return redirect('dashboard_home')
        
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    leave.status = 'Rejected'  # FIXED: Changed from 'REJECTED' to 'Rejected'
    leave.save()
    return redirect('hr_dashboard')

@login_required
def staff_directory(request):
    """Provides a searchable staff record look-up console for HR."""
    if not request.user.is_hr:
        return redirect('dashboard_home')
        
    search_query = request.GET.get('search', '')
    
    # Filter staff records dynamically if a search parameters query string is caught
    if search_query:
        staff_members = EmployeeProfile.objects.filter(
            models.Q(employee_id__icontains=search_query) |
            models.Q(user__username__icontains=search_query) |
            models.Q(designation__icontains=search_query)
        ).select_related('user', 'department')
    else:
        staff_members = EmployeeProfile.objects.select_related('user', 'department').all()
        
    return render(request, 'accounts/staff_directory.html', {
        'staff_members': staff_members,
        'search_query': search_query
    })