# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Core Authentication System
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    
    # Unified Architecture Dashboard Routing Systems
    path('dashboard/', views.dashboard_router, name='dashboard_home'),
    path('dashboard/hr/', views.hr_dashboard, name='hr_dashboard'),
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    
    # Employee Self-Service Operations (Leaves)
    path('dashboard/employee/apply-leave/', views.apply_leave, name='apply_leave'),
    path('dashboard/employee/leave-history/', views.leave_history, name='leave_history'),
    
    # HR Management Console & Operational Registry
    path('dashboard/hr/staff-directory/', views.staff_directory, name='staff_directory'),
    path('dashboard/hr/leave-requests/', views.hr_leave_requests_list, name='hr_leave_requests'),
    
    # HR Quick Action Inline Approval Mappings
    path('dashboard/hr/leave/approve/<int:leave_id>/', views.approve_leave_action, name='approve_leave_action'),
    path('dashboard/hr/leave/reject/<int:leave_id>/', views.reject_leave_action, name='reject_leave_action'),
    
    # Operational Shifts Metrics Tracker (Punch Control Endpoint)
    path('dashboard/punch/', views.punch_control, name='punch_control'),
]