from django import forms
from .models import EmployeeAllowanceDeduction, AllowanceDeduction, SalarySheetDetails, SalarySheet, \
	AllowanceDeductionEmployeeClassValue, MonthlyLogForGPF, GPFAdvanceInstallment, YearlyLogForGPF
from .calculations import SalarySheetCalculations
from datetime import datetime



class SalarySheetDetailsEditForm(forms.ModelForm):
	amount = forms.FloatField(label='')
	class Meta:
		model = SalarySheetDetails
		fields = ['amount', ]


class SalarySheetForm(forms.ModelForm):
	class Meta:
		model = SalarySheet
		fields = ['date', 'is_withdrawn','comment']
		widgets = {"date" : forms.DateInput(attrs={'class':'month-picker'})}


class SalarySheetDetailsForm(forms.ModelForm):
	amount = forms.FloatField(label='')
	class Meta:
		model = SalarySheetDetails
		fields = ['amount', ]

	def __init__(self, *args, **kwargs):
		self.allowance_deduction = kwargs.pop('allowance_deduction')
		self.title = self.allowance_deduction.name
		super().__init__(*args, **kwargs)

	def save(self, commit=True, **kwargs):
		instance = super().save(commit=False)
		salary_sheet = kwargs.pop('salary_sheet')
		instance.salary_sheet = salary_sheet
		instance.allowance_deduction = self.allowance_deduction
		if commit:
			instance.save()
		return instance


class EmployeeAllowanceDeductionForm(forms.ModelForm):

	is_applicable = forms.BooleanField(label = "", required = False)
	class Meta:
		model = EmployeeAllowanceDeduction
		fields =['is_applicable', 'value',]
		widgets = {"value": forms.NumberInput(attrs={'class': 'number-medium'})}


	def __init__(self, *args, **kwargs):
		self.allowance_deduction = kwargs.pop('allowance_deduction')
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super(EmployeeAllowanceDeductionForm, self).save(commit=False)
		instance.allowance_deduction = self.allowance_deduction
		if commit:
			instance.save()
		return instance
		

class AllowanceDeductionEmployeeClassValueForm(forms.ModelForm):
	class Meta:
		model = AllowanceDeductionEmployeeClassValue
		fields =['value']

	def __init__(self, *args, **kwargs):
		self.employee_class = kwargs.pop('employee_class')
		self.allowance_deduction = kwargs.pop('allowance_deduction')
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		instance.employee_class = self.employee_class
		instance.allowance_deduction = self.allowance_deduction
		if commit:
			instance.save()
		return instance


class ConfigureAllowanceDeductionForm (forms.ModelForm):
	is_applicable = forms.BooleanField(label = "", required = False)
	order = forms.IntegerField(label = "", required= False)
	class Meta:
		model = AllowanceDeduction
		fields = ['is_applicable', 'order']


class MonthlyProvidentFundForm(forms.ModelForm):
	class Meta:
		model = MonthlyLogForGPF
		fields = ['deduction']

	def __init__(self, *args, **kwargs):
		if 'provident_fund_profile' in kwargs:
			self.provident_fund_profile = kwargs.pop('provident_fund_profile')
		self.title = "GPF"
		super().__init__(*args, **kwargs)

	def save(self, commit=True, **kwargs):
		instance = super().save(commit=False)
		salary_sheet = kwargs.pop('salary_sheet')
		instance.salary_sheet = salary_sheet
		if not instance.id:
			instance.provident_fund_profile = self.provident_fund_profile
		if instance.provident_fund_profile.has_interest:
			instance.interest = SalarySheetCalculations.calculate_gpf_interest(salary_sheet.date,
																			   instance.deduction)
		else:
			instance.interest = 0
		if commit:
			instance.save()
		return instance
			

class GPFAdvanceInslallmentForm(forms.ModelForm):
	class Meta:
		model = GPFAdvanceInstallment
		fields = ['installment_no', 'deduction']
		widgets = {"installment_no" : forms.NumberInput(attrs={'class':'number-small'}),
					"deduction" : forms.NumberInput(attrs={'class':'number-medium'})}

	def __init__(self, *args, **kwargs):
		self.gpf_advance = kwargs.pop('gpf_advance')
		self.title = "GPF Adv.-" + str(self.gpf_advance.id)
		super().__init__(*args, **kwargs)

	def save(self, commit=True, **kwargs):
		instance = super().save(commit=False)
		instance.gpf_advance = self.gpf_advance
		salary_sheet = kwargs.pop('salary_sheet')
		instance.salary_sheet = salary_sheet
		if self.gpf_advance.provident_fund_profile.has_interest:
			instance.interest = SalarySheetCalculations.calculate_gpf_interest(salary_sheet.date,
																	   instance.deduction)
		else:
			instance.interest = 0
		if commit:
			instance.save()
		return instance

class YearlyLogForGPFFormUpdate(forms.ModelForm):
	class Meta:
		model = YearlyLogForGPF
		fields = ['net_deduction', 'net_interest', 'total_credit']


class YearlyLogForGPFFormCreate(YearlyLogForGPFFormUpdate):
	def __init__(self, *args, **kwargs):
		self.provident_fund_profile = kwargs.pop('provident_fund_profile')
		self.title = "GPF Yearly Log"
		super().__init__(*args, **kwargs)

	def save(self, commit=True, **kwargs):
		instance = super().save(commit=False)
		instance.provident_fund_profile = self.provident_fund_profile
		today = datetime.today()
		instance.date = today.replace(day=1, month=7)
		if commit:
			instance.save()
		return instance
