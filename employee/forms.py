from django import forms
from .models import Employee

class EmployeeEdit(forms.ModelForm):
	image = forms.FileField(label='Select a profile Image')
	class Meta:
		model = Employee
		fields = ['address', 'contact', 'tax_id_number', 'account_number', 'image']


