# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, Department

User = get_user_model()

class AddEmployeeForm(forms.ModelForm):
    # Explicitly expose fields to attach credentials along with the profile properties
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'
    }))

    class Meta:
        model = EmployeeProfile
        fields = ['employee_id', 'department', 'designation', 'salary']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
            'department': forms.Select(attrs={'class': 'w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
            'designation': forms.TextInput(attrs={'class': 'w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
            'salary': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'}),
        }