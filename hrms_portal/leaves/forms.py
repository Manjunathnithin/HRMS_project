from django import forms
from .models import LeaveRequest

class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        # Only expose fields the worker needs to fill out
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        
        # Inject Tailwind utility classes directly into Django's form controls
        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-slate-200 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500'
            }),
            'reason': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'w-full px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500', 
                'placeholder': 'Provide a brief reason for your leave request...'
            }),
        }