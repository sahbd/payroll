from django.db import models
from django.db.models import Sum
from django.core.urlresolvers import reverse

from duet_admin.choices import PAYMENT_TYPE, ALLOWANCE_DEDUCTION_TYPE, EMPLOYEE_CLASS, ADVANCE_CATEGORY

from autoslug import AutoSlugField


class AllowanceDeduction(models.Model):
    name = models.CharField(max_length=200, verbose_name="Name")
    description = models.TextField(null=True, blank = True, verbose_name="Description")
    code = models.CharField(max_length = 10, verbose_name = "Code", null = True)
  
    category = models.CharField(max_length=2, choices=ALLOWANCE_DEDUCTION_TYPE, verbose_name="Type")
    value = models.ManyToManyField('EmployeeClass', through='AllowanceDeductionEmployeeClassValue')
    is_percentage = models.BooleanField(verbose_name="Percentage")
    is_applicable = models.BooleanField(verbose_name="Applicable")
    payment_type = models.CharField(max_length=2, choices=PAYMENT_TYPE, default='m', verbose_name="Payment Type")
    order = models.IntegerField(null= True, blank = True, verbose_name='Order')

    created_at = models.DateTimeField(auto_now_add = True, auto_now = False, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")

    slug = AutoSlugField(populate_from='name', unique_with='id', always_update=True, default=None)

    class Meta:
    	ordering = ['order']
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('duet_admin:allowancededuction-list')


class EmployeeAllowanceDeduction(models.Model):
    value = models.FloatField(verbose_name='Value', default=0, blank=True)
    is_applicable = models.BooleanField(verbose_name='Applicable')
    employee = models.ForeignKey('employee.Employee', on_delete=models.PROTECT)
    allowance_deduction = models.ForeignKey( AllowanceDeduction, verbose_name='Name', on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add = True, auto_now = False, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")

    def __str__(self):
        return self.allowance_deduction.name

    class Meta:
        unique_together = ("employee", "allowance_deduction")
        ordering = ['allowance_deduction__order']
            

class SalarySheet(models.Model):
    employee = models.ForeignKey('employee.Employee', verbose_name= 'Employee')
    date = models.DateField(verbose_name = 'Month Ending')
    is_freezed = models.BooleanField(default=False, verbose_name= 'Freezed')
    is_withdrawn = models.BooleanField(default = True, verbose_name='Withdrawn')

    allowance_deductions = models.ManyToManyField(AllowanceDeduction, through='SalarySheetDetails')
    
    comment = models.TextField(null = True, blank = True)
    created_at = models.DateTimeField(auto_now_add = True, auto_now = False, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")

    class Meta:
        ordering = ['-modified_at']
    
    def get_net_allowance(self):
        allowance = SalarySheetDetails.objects.filter(salary_sheet = self).exclude(allowance_deduction__category = 'd').aggregate(total=Sum("amount"))['total']
        if allowance is None:
            allowance = 0
        return allowance
    
    def get_net_deduction(self):
        deduction = SalarySheetDetails.objects.filter(salary_sheet = self, allowance_deduction__category = 'd').aggregate(total=Sum("amount"))['total']
        if deduction is None:
             deduction = 0
        try:
            gpf_subscription_deduction = MonthlyLogForGPF.objects.get(salary_sheet = self)
            deduction = deduction + gpf_subscription_deduction.deduction
        except MonthlyLogForGPF.DoesNotExist:
            pass

        gpf_advances_deduction = GPFAdvanceInstallment.objects.filter(salary_sheet=self).aggregate(total = Sum(
            "deduction"))['total']
        if gpf_advances_deduction is not None:
            deduction = deduction + gpf_advances_deduction

        return deduction

    def get_total_payment(self):
        return self.get_net_allowance() - self.get_net_deduction()

    net_allowance= property(get_net_allowance)
    net_deduction = property(get_net_deduction)
    total_payment = property(get_total_payment)

    def __str__(self):
        return 'Salary Sheet-' + str(self.id) + "-" +  self.date.strftime("%B") + ',' + str(self.date.year)


class SalarySheetDetails(models.Model):
    salary_sheet = models.ForeignKey(SalarySheet, on_delete=models.CASCADE)
    allowance_deduction = models.ForeignKey(AllowanceDeduction, on_delete=models.PROTECT)
    amount = models.FloatField(default = 0)

    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")

    class Meta:
        ordering = ['allowance_deduction__order']


class EmployeeClass(models.Model):
    name = models.CharField(max_length= 50, verbose_name= 'Title')
    description = models.TextField(verbose_name = 'Description', null = True, blank = 'True')

    created_at = models.DateTimeField(auto_now_add = True, auto_now = False, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")

    slug = AutoSlugField(populate_from='name', unique_with='id', always_update=True, default=None)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('duet_admin:employee-class-list')


class AllowanceDeductionEmployeeClassValue(models.Model):
    value = models.FloatField()
    allowance_deduction = models.ForeignKey(AllowanceDeduction)
    employee_class = models.ForeignKey(EmployeeClass)

    class Meta:
        unique_together = ("employee_class", "allowance_deduction")
    

class Grade(models.Model):
    grade_no = models.IntegerField(verbose_name= 'Grade')
    description = models.TextField(verbose_name = 'Description', null = True, blank = 'True')
    employee_class = models.ForeignKey(EmployeeClass, verbose_name= 'Class')

    created_at = models.DateTimeField(auto_now_add = True, auto_now = False, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")

    slug = AutoSlugField(populate_from='grade_no', unique_with='id', always_update=True, default=None)

    def __str__(self):
        return 'Grade-' + str(self.grade_no)

    def get_absolute_url(self):
        return reverse('duet_admin:grade-list')


class ProvidentFundProfile(models.Model):
    employee = models.OneToOneField('employee.Employee', on_delete=models.CASCADE, verbose_name='Employee')
    has_interest = models.BooleanField(verbose_name="Interest Taken", default=True)
    percentage = models.IntegerField(verbose_name='Percentage', default=0)

    def __str__(self):
        return 'GPF Profile of ' + self.employee.get_full_name()


class MonthlyLogForGPF(models.Model):
    salary_sheet = models.ForeignKey('duet_account.SalarySheet', verbose_name='Salary Sheet', on_delete= models.CASCADE)
    deduction = models.FloatField(verbose_name= 'Deduction', default=0)
    interest = models.FloatField(verbose_name='Interest', default=0)

    provident_fund_profile = models.ForeignKey(ProvidentFundProfile, verbose_name='Employee', on_delete=models.PROTECT)

    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")

    def get_absolute_url(self):
        return reverse('duet_account:provident-fund-monthly-logs')

    class Meta:
        ordering = ['salary_sheet__date']


class YearlyLogForGPF(models.Model):
    date = models.DateField(verbose_name='Year Ending')
    net_deduction = models.FloatField(verbose_name='Net Deduction')
    net_interest = models.FloatField(verbose_name='Net Interest')
    total_credit = models.FloatField(verbose_name='Total')
    is_freezed = models.BooleanField(verbose_name='Freezed', default=False)

    provident_fund_profile = models.ForeignKey(ProvidentFundProfile, verbose_name='Employee', on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now=True, verbose_name="Modified At")

    def __str__(self):
        return 'GPF Yearly Log - ' + str(self.id)


class GPFAdvance(models.Model):
    provident_fund_profile = models.ForeignKey(ProvidentFundProfile, verbose_name='Employee', on_delete=models.PROTECT)
    amount = models.FloatField('Amount')
    no_of_installments = models.IntegerField(verbose_name= 'No of Installments')
    monthly_payment = models.FloatField(verbose_name='Monthly Payment')
    date = models.DateField(verbose_name= 'Date')
    is_closed = models.BooleanField(verbose_name='Closed', default= False)
    closing_date = models.DateField(verbose_name='Closing Date', null = True, blank = True)

    created_at = models.DateTimeField(auto_now_add = True, auto_now = False, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")

    def _get_last_installment_number(self):
        last_installment = GPFAdvanceInstallment.objects.filter(gpf_advance = self).last()
        if last_installment is None:
            return 0
        return last_installment.installment_no

    def get_absolute_url(self):
        return reverse('duet_account:gpf-advance-list')

    def __str__(self):
        return 'GPF Advance - ' + str(self.id)


class GPFAdvanceInstallment(models.Model):
    gpf_advance = models.ForeignKey(GPFAdvance, verbose_name='GPF Advance', on_delete=models.PROTECT)
    installment_no = models.IntegerField(verbose_name='Install No.')
    deduction = models.FloatField(verbose_name='Deduction')
    interest = models.FloatField(verbose_name='Interest', default=0)

    salary_sheet = models.ForeignKey('duet_account.SalarySheet', verbose_name='Salary Sheet', on_delete= models.CASCADE)

    modified_at = models.DateTimeField(auto_now = True, verbose_name="Modified At")
    
    class Meta:
        ordering = ['installment_no']
