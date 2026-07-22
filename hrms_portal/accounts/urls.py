from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    
    path('dashboard/', views.dashboard_router, name='dashboard_home'),
    path('dashboard/hr/', views.hr_dashboard, name='hr_dashboard'),
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    
    path('punch/', views.punch_control, name='punch_control'),
    
    path('leave/apply/', views.apply_leave, name='apply_leave'),
    path('leave/history/', views.leave_history, name='leave_history'),

    path('dashboard/hr/leave-action/approve/<int:leave_id>/', views.approve_leave_action, name='approve_leave_action'),
    path('dashboard/hr/leave-action/reject/<int:leave_id>/', views.reject_leave_action, name='reject_leave_action'),
    path('dashboard/hr/leave-requests/', views.hr_leave_requests_list, name='hr_leave_requests'),
    path('dashboard/hr/staff-directory/toggle-status/<int:user_id>/', views.toggle_staff_active_status, name='toggle_staff_active_status'),
    path('dashboard/hr/staff-directory/delete/<int:user_id>/', views.delete_staff_profile, name='delete_staff_profile'),
    
    path('dashboard/hr/staff-directory/', views.staff_directory, name='staff_directory'),

    path('dashboard/hr/staff-directory/toggle-status/<int:user_id>/', views.toggle_staff_active_status, name='toggle_staff_active_status'),
    path('dashboard/hr/staff-directory/delete/<int:user_id>/', views.delete_staff_profile, name='delete_staff_profile'),
    path('dashboard/hr/staff-directory/export-csv/', views.export_staff_csv, name='export_staff_csv'),

    #Announcement urls
    path('dashboard/hr/post-announcements/', views.post_announcement, name='post_announcement'),
]