import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum, Count
from django.contrib import messages
from django.core.mail import send_mail 
import random
from django.contrib.auth import authenticate, login as auth_login
from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect

from employees.models import EmployeeProfile, Department
from leaves.models import LeaveRequest, LeaveBalance
from leaves.forms import LeaveApplicationForm
from .models import User, EmployeeProfile, Department
from .forms import AddEmployeeForm

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        # Standard username/password collection
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Generate a secure 6-digit OTP code token
            otp_code = str(random.randint(100000, 999999))
            
            # Temporary stage user credentials inside the safe session storage layer
            request.session['pre_auth_user_id'] = user.id
            request.session['login_otp_token'] = otp_code
            
            recipient_email = user.email
            if not recipient_email:
                recipient_email = 'employee-registration-pending@company.com'
            # Send the OTP via the email service
            send_mail(
                subject="HRMS Secure Login Access Token Alert",
                message=(
                    f"Hello {user.username},\n\n"
                    f"A login request was made for your HRMS profile account.\n"
                    f"Your Security Verification OTP is: {otp_code}\n\n"
                    f"This verification parameter code remains active for this login window session context."
                ),
                from_email='security@hrms-portal.com',
                recipient_list=[user.email if user.email else 'employee@company.com'],
                fail_silently=False
            )
            
            messages.info(request, "A security verification OTP code has been dispatched to your email address!")
            return redirect('verify_otp')
        else:
            messages.error(request, "Invalid corporate login credentials. Please review entries.")
            
    return render(request, 'accounts/login.html')

@csrf_protect
def verify_otp(request):
    # Route guard safety check: block access if user didn't successfully finish stage-1 form
    user_id = request.session.get('pre_auth_user_id')
    saved_otp = request.session.get('login_otp_token')
    
    if not user_id or not saved_otp:
        messages.error(request, "Unauthorized sequence vector access attempt blocked.")
        return redirect('login')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp_token')
        
        if entered_otp == saved_otp:
            # Lookup the structural record matching the user context identity
            from .models import User
            user = User.objects.get(id=user_id)
            
            # Formally authenticate and sign them into the active browser cookie thread
            auth_login(request, user)
            
            # Secure clean-up of temporary setup keys from backend state mapping records
            del request.session['pre_auth_user_id']
            del request.session['login_otp_token']
            
            messages.success(request, f"Welcome back, {user.username}! Access authorization approved.")
            
            # Direct dynamically according to role settings
            if user.is_hr:
                return redirect('hr_dashboard')
            return redirect('employee_dashboard')
        else:
            messages.error(request, "Incorrect OTP entry token code submitted. Please review values.")
            
    return render(request, 'accounts/verify_otp.html')

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

            emp_id = getattr(request.user.profile, 'employee_id', 'N/A')

            send_mail(
                subject=f"New Leave Application Alert: {request.user.username} ({emp_id})",
                message=(
                    f"Employee {request.user.username}\n"
                    f"Employee ID: {emp_id}\n"
                    f"leave Type: {leave_instance.leave_type}\n\n"
                    f"Details: {request.user.username} has submitted a new leave request for review."
                ),
                from_email='system@hrms-portal.com',
                recipient_list=['hr-admin@company.com'],
                fail_silently=True
            )
            messages.success(request, "Leave request submitted successfully.")
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

    # Process form action if HR attempts to create a new personnel profile record
    if request.method == 'POST':
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            # 1. Spawn base credentials user object entry first
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            new_user = User.objects.create_user(username=username, email=email, password=password, is_employee=True)
            
            # 2. Map structural profile fields to it
            profile = form.save(commit=False)
            profile.user = new_user
            profile.save()
            
            messages.success(request, f"Successfully provisioned corporate profile registry for {username}!")
            return redirect('staff_directory')
    else:
        form = AddEmployeeForm()
    
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
        'search_query': search_query,
        'form': form
    })

@login_required
def leave_history(request):
    """Provides a complete paginated historical log of all time-off entries for a worker."""
    if not request.user.is_employee:
        return redirect('dashboard_home')
        
    # Fetch all leave records for this specific logged-in user
    all_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-applied_on')
    
    return render(request, 'accounts/leave_history.html', {
        'all_leaves': all_leaves
    })