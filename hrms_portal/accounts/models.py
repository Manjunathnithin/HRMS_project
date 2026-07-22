from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from datetime import datetime

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
    avatar = models.ImageField(upload_to='avatars/',blank=True, null=True)

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
        unique_together = ['user', 'date'] # One structural registry entry block per person per day

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    @property
    def total_working_hours(self):
        """Computes the exact duration metric profile output for a processed shift."""
        if self.punch_in and self.punch_out:
            duration = self.punch_out - self.punch_in
            total_seconds = duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        return "Active Shift/Incomplete"

    @property
    def total_working_hours(self):
        if self.punch_in and self.punch_out:
            duration = self.punch_out - self.punch_in
            total_seconds = int(duration.total_seconds())
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        elif self.punch_in:
            return "Session Active"
        return "Incomplete Shift"

