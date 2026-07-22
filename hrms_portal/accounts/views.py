import random
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q 
from django.http import HttpResponse

from .models import User, Attendance, Department
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
            otp_code = str(random.randint(100000, 999999))
            request.session['pre_auth_user_id'] = user.id
            request.session['login_otp_token'] = otp_code
            
            recipient_email = user.email
            if not recipient_email:
                recipient_email = 'employee-registration-pending@company.com'
            
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
            auth_login(request, user)
            
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
    
    total_staff = User.objects.filter(is_hr=False).count()
    pending_leaves = LeaveRequest.objects.filter(status='Pending').count()
    total_payroll = 450000 
    
    recent_requests = LeaveRequest.objects.all().order_by('-id')[:5]
    attendance = Attendance.objects.filter(user=request.user, date=today).first()
    live_attendance_logs = Attendance.objects.all().select_related('user').order_by('-date', 'punch_in')[:7]
    
    department_counts = User.objects.filter(is_hr=False).values('profile__department__name').annotate(total=Count('id'))
    
    chart_labels = []
    chart_data = []
    
    for item in department_counts:
        dept_name = item['profile__department__name'] if item['profile__department__name'] else 'Unassigned'
        chart_labels.append(dept_name)
        chart_data.append(item['total'])
        
    if not chart_labels:
        chart_labels = ['No Staff Logged']
        chart_data = [0]
    
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
    my_leaves = LeaveRequest.objects.filter(user=request.user).order_by('-id')[:5]
    approved_count = LeaveRequest.objects.filter(user=request.user, status='Approved').count()
    pending_count = LeaveRequest.objects.filter(user=request.user, status='Pending').count()
    attendance = Attendance.objects.filter(user=request.user, date=today).first()
    shift_logs = Attendance.objects.filter(user=request.user).order_by('-date')[:7]
    
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
        'shift_logs': shift_logs,
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
            leave_request.user = request.user
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


# ==============================================================================
# 6. STAFF DIRECTORY MANAGEMENT CONSOLE (MANUAL EMPLOYEE ID ASSIGNMENT)
# ==============================================================================

@login_required
@hr_required
def staff_directory(request):
    """Handles manual creation of staff members and active directory searching safely."""
    from .models import User, Department 
    
    # --- HANDLE NEW ACCOUNT PROVISIONING (POST) ---
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        employee_id = request.POST.get('employee_id', '').strip()
        department_id = request.POST.get('department')
        designation = request.POST.get('designation', '').strip()
        salary_raw = request.POST.get('salary', '0').strip()
        
        try:
            salary = float(salary_raw) if salary_raw else 0.0
        except ValueError:
            salary = 0.0
        
        if username and password:
            if User.objects.filter(username__iexact=username).exists():
                messages.error(request, f"The username '{username}' is already taken.")
            else:
                try:
                    new_user = User.objects.create_user(
                        username=username, email=email, password=password, is_hr=False
                    )
                    
                    profile_model = User.profile.related.related_model
                    profile, created = profile_model.objects.get_or_create(user=new_user)
                    
                    dept_obj = None
                    if department_id:
                        dept_obj = Department.objects.filter(id=department_id).first()
                    
                    profile.employee_id = employee_id
                    profile.designation = designation if designation else "Staff Member"
                    profile.salary = salary
                    profile.department = dept_obj
                    profile.save()
                    
                    messages.success(request, f"Profile for '{username}' successfully built!")
                    return redirect('staff_directory')
                except Exception as e:
                    messages.error(request, f"Account provision failure: {str(e)}")
        else:
            messages.error(request, "Username and password specifications are mandatory.")

    # --- HANDLE DIRECTORY RENDERING (GET) SAFELY ---
    raw_staff = User.objects.filter(is_hr=False).select_related('profile').defer('profile__salary')

    search_query = request.GET.get('search', '').strip()
    if search_query:
        raw_staff = raw_staff.filter(
            Q(username__icontains=search_query) |
            Q(profile__employee_id__icontains=search_query) |
            Q(profile__designation__icontains=search_query) |
            Q(profile__department__name__icontains=search_query)
        )
    
    staff_members = []
    for member in raw_staff:
        # Safe fallback: manually read or default if database value is corrupted
        try:
            val = getattr(member.profile, 'salary', 0)
            member.display_salary = float(val) if val else 0.0
        except Exception:
            member.display_salary = 0.0
            
        staff_members.append(member)
    departments = Department.objects.all()
    
    context = {
        'staff_members': staff_members,
        'search_query': search_query,
        'departments': departments,
    }
    return render(request, 'accounts/staff_directory.html', context)

@login_required
@hr_required
def hr_leave_requests_list(request):
    """Displays a complete historical grid table overview of all employee leave applications for HR."""
    all_requests = LeaveRequest.objects.all().order_by('-id')
    return render(request, 'accounts/hr_leave_requests.html', {'all_requests': all_requests})

@login_required
@hr_required
def toggle_staff_active_status(request, user_id):
    staff_user = get_object_or_404(User, id=user_id, is_hr=False)
    staff_user.is_active = not staff_user.is_active
    staff_user.save()
    status_msg = "activated" if staff_user.is_active else "deactivated"
    messages.success(request, f"Account for '{staff_user.username}' has been successfully {status_msg}.")
    return redirect('staff_directory')


@login_required
@hr_required
def delete_staff_profile(request, user_id):
    staff_user = get_object_or_404(User, id=user_id, is_hr=False)
    username = staff_user.username
    staff_user.delete()
    messages.warning(request, f"Profile for '{username}' has been permanently removed.")
    return redirect('staff_directory')


@login_required
@hr_required
def export_staff_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="staff_directory_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Username', 'Email', 'Employee ID', 'Department', 'Designation', 'Monthly Salary (INR)', 'Account Status'])

    raw_staff = User.objects.filter(is_hr=False).select_related('profile')
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        raw_staff = raw_staff.filter(
            Q(username__icontains=search_query) |
            Q(profile__employee_id__icontains=search_query) |
            Q(profile__designation__icontains=search_query) |
            Q(profile__department__name__icontains=search_query)
        )

    for member in raw_staff:
        profile = getattr(member, 'profile', None)
        emp_id = profile.employee_id if profile and profile.employee_id else '--'
        dept = profile.department.name if profile and profile.department else 'Unassigned'
        designation = profile.designation if profile and profile.designation else '--'
        salary = profile.salary if profile and profile.salary else 0
        status = 'Active' if member.is_active else 'Disabled'

        writer.writerow([member.username, member.email, emp_id, dept, designation, salary, status])

    return response