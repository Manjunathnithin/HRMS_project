from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

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

class LeaveBalance(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_balance')
    sick_leave_remaining = models.IntegerField(default=12)      # 12 days yearly default
    personal_leave_remaining = models.IntegerField(default=15)  # 15 days yearly default
    casual_leave_remaining = models.IntegerField(default=10)    # 10 days yearly default

    def __str__(self):
        return f"{self.user.username}'s Quota Balance"

# Database signal trigger to auto-deduct days when a leave is marked as Approved
@receiver(post_save, sender=LeaveRequest)
def auto_deduct_leave_balance(sender, instance, **kwargs):
    if instance.status == 'Approved':
        # Safely fetch or initialize the worker's quota block
        balance, created = LeaveBalance.objects.get_or_create(user=instance.user)
        days_taken = instance.duration_days
        
        if instance.leave_type == 'SL':
            balance.sick_leave_remaining = max(0, balance.sick_leave_remaining - days_taken)
        elif instance.leave_type == 'PL':
            balance.personal_leave_remaining = max(0, balance.personal_leave_remaining - days_taken)
        elif instance.leave_type == 'CL':
            balance.casual_leave_remaining = max(0, balance.casual_leave_remaining - days_taken)
            
        balance.save()