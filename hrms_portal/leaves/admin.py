from django.contrib import admin
from .models import LeaveRequest
# Register your models here.

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status', 'duration_days', 'applied_on')
    list_filter = ('status', 'leave_type')
    search_fields = ('user__username', 'reason')
    
    # Custom action inside admin to approve multiple leaves at once
    actions = ['approve_leaves', 'reject_leaves']

    def approve_leaves(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_leaves.short_description = "Mark selected requests as Approved"

    def reject_leaves(self, request, queryset):
        queryset.update(status='REJECTED')
    reject_leaves.short_description = "Mark selected requests as Rejected"