import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils import timezone

from .models import User, Attendance
from leaves.models import LeaveRequest
from leaves.forms import LeaveApplicationForm
from .decorators import hr_required, employee_required


# ==============================================================================
# 1. CORE TWO-FACTOR AUTHENTICATION SYSTEM (STAGE 1 & STAGE 2)
# ==============================================================================

@csrf_protect
def login_view(request):
    """Handles standard credential collection and initiates 2FA sequence."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Generate a secure 6-digit OTP token
            otp_code = str(random.randint(100000, 999999))
            
            # Temporary stage user credentials inside the safe session storage layer
            request.session['pre_auth_user_id'] = user.id
            request.session['login_otp_token'] = otp_code
            
            # Dynamic Email Routing: Target the exact logging user's email address
            recipient_email = user.email
            if not recipient_email:
                recipient_email = 'employee-registration-pending@company.com'
            
            # Fire real email transaction over live network SMTP pipeline
            from django.core.mail import send_mail
            send_mail(
                subject="HRMS Secure Login Access Token Alert",
                message=(
                    f"Hello {user.username},\n\n"
                    f"A login request was made for your HRMS profile account.\n"
                    f"Your Security Verification OTP is: {otp_code}\n\n"
                    f"This verification parameter code remains active for this login window session context."
                ),
                from_email='security@hrms-portal.com',
                recipient_list=[recipient_email],
                fail_silently=False
            )
            
            messages.info(request, "A security verification OTP code has been dispatched to your email address!")
            return redirect('verify_otp')
        else:
            messages.error(request, "Invalid corporate login credentials. Please review entries.")
            
    return render(request, 'accounts/login.html')


@csrf_protect
def verify_otp(request):
    """Verifies session tokens and completes authentication sequence entry points."""
    user_id = request.session.get('pre_auth_user_id')
    saved_otp = request.session.get('login_otp_token')
    
    if not user_id or not saved_otp:
        messages.error(request, "Unauthorized sequence vector access attempt blocked.")
        return redirect('login')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp_token')
        
        if entered_otp == saved_otp:
            user = User.objects.get(id=user_id)
            
            # Sign them formally into the active web session thread
            auth_login(request, user)
            
            # Secure cleanup using pop(key, None) to prevent KeyError exceptions
            request.session.pop('pre_auth_user_id', None)
            request.session.pop('login_otp_token', None)
            
            messages.success(request, f"Welcome back, {user.username}! Access authorization approved.")
            return redirect('dashboard_home')
        else:
            messages.error(request, "Incorrect OTP entry token code submitted. Please review values.")
            
    return render(request, 'accounts/verify_otp.html')


# ==============================================================================
# 2. CORE DASHBOARD LAYER & DYNAMIC BALANCES ROUTER
# ==============================================================================

@login_required
def dashboard_router(request):
    """Bridges entryways, dividing staff users from administrative management."""
    if request.user.is_hr:
        return redirect('hr_dashboard')
    return redirect('employee_dashboard')


@login_required
@hr_required
def hr_dashboard(request):
    """Renders HR management metrics along with incoming leave data flows."""
    today = timezone.localdate()
    
    # 1. Gather Metric Dashboard Readouts
    total_staff = User.objects.filter(is_hr=False).count()
    pending_leaves = LeaveRequest.objects.filter(status='Pending').count()
    
    # Dynamic computation placeholder for dashboard tracking metrics
    total_payroll = 450000 
    
    # 2. Extract recent leave requests pipeline data 
    recent_requests = LeaveRequest.objects.all().order_by('-id')[:5]
    
    # 3. Dynamic Attendance Toggle Data Fetch (Ensures the Single Button functions correctly)
    attendance = Attendance.objects.filter(user=request.user, date=today).first()
    live_attendance_logs = Attendance.objects.all().select_related('user').order_by('-date', 'punch_in')[:7]
    # 4. Department chart data breakdown logic placeholder variables
    chart_labels = ['Operations', 'Technology', 'Finance', 'HR Support']
    chart_data = [12, 19, 5, 2]
    
    context = {
        'total_staff': total_staff,
        'pending_leaves': pending_leaves,
        'total_payroll': total_payroll,
        'recent_requests': recent_requests,
        'attendance': attendance,
        'live_attendance_logs': live_attendance_logs,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'accounts/hr_dashboard.html', context)


@login_required
@employee_required
def employee_dashboard(request):
    """Renders employee dashboard metrics along with personal leave data balances."""
    today = timezone.localdate()
    profile = getattr(request.user, 'profile', None)
    
    # Fetch leave requests and metric summary details
    my_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-id')[:5]
    approved_count = LeaveRequest.objects.filter(user=request.user, status='Approved').count()
    pending_count = LeaveRequest.objects.filter(user=request.user, status='Pending').count()
    
    # Dynamic Attendance Toggle Data Fetch (Ensures the Single Button functions correctly)
    attendance = Attendance.objects.filter(user=request.user, date=today).first()
    shift_logs = Attendance.objects.filter(user=request.user).order_by('-date')[:7]
    # Safe structure mappings for available quota balances
    balances = {
        'sick_leave_remaining': getattr(profile, 'sick_leave_balance', 15),
        'personal_leave_remaining': getattr(profile, 'personal_leave_balance', 10),
        'casual_leave_remaining': getattr(profile, 'casual_leave_balance', 12),
    }
    
    context = {
        'profile': profile,
        'my_leaves': my_leaves,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'attendance': attendance,
        'shift_logs' : shift_logs,
        'balances': balances,
    }
    return render(request, 'accounts/employee_dashboard.html', context)


# ==============================================================================
# 3. ATTENDANCE SHIFT TRACKING LAYER (PUNCH IN / PUNCH OUT)
# ==============================================================================

@login_required
def punch_control(request):
    """Manages structural shift terminal lifecycles inside a single action button."""
    today = timezone.localdate()
    attendance, created = Attendance.objects.get_or_create(user=request.user, date=today)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'punch_in' and not attendance.punch_in:
            attendance.punch_in = timezone.now()
            attendance.save()
            messages.success(request, "Shift session started successfully! Punch-in recorded.")
            
        elif action == 'punch_out' and attendance.punch_in and not attendance.punch_out:
            attendance.punch_out = timezone.now()
            attendance.save()
            messages.success(request, "Shift session finalized! Punch-out recorded.")
            
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_home'))


# ==============================================================================
# 4. EMPLOYEE LEAVE APPLICATION PROCESSING & HISTORIES
# ==============================================================================

@login_required
def apply_leave(request):
    """Processes new form applications and alerts via notification mail."""
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.user = request.user  # Tie the current logged-in user to this leave
            leave_request.status = 'Pending'
            leave_request.save()
            
            messages.success(request, "Leave request submitted successfully! Pending HR verification.")
            return redirect('employee_dashboard')
        else:
            messages.error(request, "Form validation failed. Please inspect field input bounds.")
    else:
        form = LeaveApplicationForm()
    return render(request, 'accounts/apply_leave.html', {'form': form})


@login_required
def leave_history(request):
    """Provides a chronological grid overview of full log histories."""
    all_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-id')
    return render(request, 'accounts/leave_history.html', {'all_leaves': all_leaves})


# ==============================================================================
# 5. HR QUICK ACTION ADMINISTRATIVE OPERATIONAL OVERRIDES
# ==============================================================================

@login_required
def approve_leave_action(request, leave_id):
    """Validates parameters and updates leave status to Approved."""
    if not request.user.is_hr:
        messages.error(request, "Access Denied. HR administrative credentials required.")
        return redirect('dashboard_home')
        
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if leave.status == 'Pending':
        leave.status = 'Approved'
        leave.save()
        messages.success(request, f"Leave application request for {leave.user.username} approved.")
    return redirect(request.META.get('HTTP_REFERER', 'hr_dashboard'))


@login_required
def reject_leave_action(request, leave_id):
    """Validates parameters and updates leave status to Rejected."""
    if not request.user.is_hr:
        messages.error(request, "Access Denied. HR administrative credentials required.")
        return redirect('dashboard_home')
        
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if leave.status == 'Pending':
        leave.status = 'Rejected'
        leave.save()
        messages.warning(request, f"Leave application request for {leave.user.username} rejected.")
    return redirect(request.META.get('HTTP_REFERER', 'hr_dashboard'))


@login_required
def staff_directory(request):
    """Displays directory list profiles across all company branches."""
    staff_members = User.objects.filter(is_hr=False).select_related('profile')
    return render(request, 'accounts/staff_directory.html', {'staff_members': staff_members})

@login_required
@hr_required
def hr_leave_requests_list(request):
    """Displays a complete historical grid table overview of all employee leave applications for HR."""
        
    # Fetch all leave requests ordered by newest first
    all_requests = LeaveRequest.objects.all().order_by('-id')
    
    return render(request, 'accounts/hr_leave_requests.html', {'all_requests': all_requests})