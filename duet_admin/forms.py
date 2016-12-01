from django import forms
from employee.models import Employee

			
class EmployeeCreateForm(forms.ModelForm):
	class Meta:
		model = Employee
		fields = ['username','first_name','last_name', 'email' ,'address', 'gender', 'dob', 'joining_date',
				  'designation', 'grade','department']
		widgets = {
            'dob': forms.DateInput(attrs={'class':'date-picker'}),
            'joining_date': forms.DateInput(attrs={'class':'date-picker'}),
        }

	def save(self, commit=True):
		# Save the provided password in hashed format
		employee = super().save(commit=False)
		employee.set_password(self.cleaned_data["first_name"])
		if commit:
			employee.save()
		return employee


class EmployeeUpdateForm(forms.ModelForm):
	class Meta:
		model = Employee
		fields = ['first_name','last_name', 'email' ,'address', 'gender', 'dob', 'joining_date',
				  'designation', 'grade','department']

		widgets = {'dob': forms.DateInput(attrs={'class': 'date-picker'}),
			'joining_date': forms.DateInput(attrs={'class': 'date-picker'}), }


class AssignUserToGroupForm(forms.ModelForm):
	class Meta:
		model = Employee
		fields = ['groups']
		widgets = {"groups": forms.CheckboxSelectMultiple()}