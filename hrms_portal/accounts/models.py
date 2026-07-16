from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    is_hr = models.BooleanField(
        default=False,
        help_text="Designates whether this user is an HR user."
    )
    is_employee=models.BooleanField(
        default=True,
        help_text="Designates whether this user is an Employee user."
    )

    def __str__(self):
        return f"{self.username} ({'HR' if self.is_hr else 'Employee'})"

