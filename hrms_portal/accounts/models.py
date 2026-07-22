from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    """Custom User Model that extends base corporate security credentials."""
    is_employee = models.BooleanField(default=False)
    is_hr = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Department(models.Model):
    """Stores structural company departments."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class EmployeeProfile(models.Model):
    """Stores professional and financial attributes for staff members."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    designation = models.CharField(max_length=100)
    joining_date = models.DateField(auto_now_add=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # Added Leave Quota Balances
    sick_leave_balance = models.IntegerField(default=15)
    personal_leave_balance = models.IntegerField(default=10)
    casual_leave_balance = models.IntegerField(default=12)

    def __str__(self):
        return f"{self.user.username} - {self.employee_id}"


class Attendance(models.Model):
    """Tracks daily shift log timings, session lifetimes, and clock states."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_logs')
    date = models.DateField(auto_now_add=True)
    punch_in = models.DateTimeField(null=True, blank=True)
    punch_out = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    @property
    def total_working_hours(self):
        """Computes the exact duration metric output for a processed shift."""
        if self.punch_in and self.punch_out:
            duration = self.punch_out - self.punch_in
            total_seconds = int(duration.total_seconds())
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        elif self.punch_in:
            return "Session Active"
        return "Incomplete Shift"


class LeaveRequest(models.Model):
    """Stores employee time-off applications and approval statuses."""
    LEAVE_TYPES = (
        ('SL', 'Sick Leave'),
        ('PL', 'Personal Leave'),
        ('CL', 'Casual Leave'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=2, choices=LEAVE_TYPES, default='CL')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_leave_type_display()} ({self.status})"


class Announcement(models.Model):
    """Model for HR company-wide notices and broadcast messages."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title