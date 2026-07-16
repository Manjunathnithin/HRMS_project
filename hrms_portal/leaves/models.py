from django.db import models
from django.conf import settings
# Create your models here.

class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('SL', 'Sick Leave'),
        ('PL', 'Personal Leave'),
        ('CL', 'Casual Leave'),
        ('UL', 'Unpaid Leave'),
    ]
    STATUS_CHOICES = [
        ('Pending','Pending'),
        ('Approved','Approved'),
        ('Rejected','Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name = 'leave_request')
    leave_type = models.CharField(max_length=2, choices=LEAVE_TYPES, default = 'CA')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True, null=True)

    #status feild
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default = 'Pending')
    applied_on = models.DateTimeField(auto_now_add=True)
    comment_by_hr= models.TextField(blank=True, null=True,help_text="Rejection reasons from HR")

    class Meta:
        ordering = ['-applied_on']

    def __str__(self):
        return f"{self.user.username} - {self.get_leave_type_display()} ({self.status})"
    
    @property
    def duration_days(self):
        """ calculates total days taken for metric tracking"""
        if self.end_date and self.start_date:
            return (self.end_date - self.start_date).days +1
        return 0
    