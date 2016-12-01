from django.views.generic import DetailView
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, redirect

from .models import Employee
from duet_account.models import EmployeeAllowanceDeduction, GPFAdvanceInstallment, MonthlyLogForGPF, GPFAdvance, \
    SalarySheet

from braces.views import LoginRequiredMixin
from duet_account.salarySheet import SalarySheetDetail
from duet_account.providentFund import ProvidentFundAdvanceDetail

from duet_admin.utils import CustomTableView, CustomUpdateView


class EmployeeProfileUpdate(LoginRequiredMixin, CustomUpdateView):
    model = Employee
    fields = ['first_name', 'last_name', 'contact', 'address', 'tax_id_number', 'account_number']
    template_name = 'employee/employee/detail_form.html'
    cancel_url = 'employee-profile'
    title = 'Edit'

    def get_object(self, queryset=None):
        user = self.request.user
        return Employee.objects.get(user_ptr=user)

    def get_success_url(self):
        return reverse_lazy('employee-profile')


class EmployeeDetailBase(object):
    def get(self, request, *args, **kwargs):
        user = self.request.user
        self.employee = Employee.objects.get(user_ptr=user)
        return super().get(request, args, kwargs)


class EmployeeProfile(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'employee/employee/detail.html'
    context_object_name = 'employee'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        self.object = Employee.objects.get(user_ptr=user)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class EmployeeSalaryList(LoginRequiredMixin, EmployeeDetailBase, CustomTableView):
    template_name = 'employee/employee/detail_list.html'
    model = SalarySheet
    fields = ['id', 'date', 'is_withdrawn', 'net_allowance', 'net_deduction', 'total_payment']
    filter_fields = {'id': ['icontains'], 'date': ['exact'],}
    title = 'Salary Sheet List'

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        employee = self.employee
        return qs.filter(employee=employee, is_freezed=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    actions = [
        {'url': 'employee-salary-sheet-detail', 'icon': 'glyphicon glyphicon-th-large', 'tooltip': 'Detail'},
    ]


class EmployeeSalarySheetDetail(LoginRequiredMixin, SalarySheetDetail):
    template_name = 'employee/employee/salarySheet/detail.html'


class EmployeeAllowanceDeductionList(LoginRequiredMixin, CustomTableView):
    model = EmployeeAllowanceDeduction
    template_name = 'employee/employee/detail_list.html'
    fields = ['allowance_deduction', 'value', 'is_percentage', 'is_applicable']
    filter_fields = {'allowance_deduction__name': ['icontains'],
                     'allowance_deduction__category': ['exact'],}

    def get(self, request, *args, **kwargs):
        user = self.request.user
        self.employee = Employee.objects.get(user_ptr=user)
        return super().get(request, args, kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        employee = self.employee
        return qs.filter(employee=employee)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.employee
        context['employee'] = employee
        return context

    title = 'Pay, Allowance and Deductions'


########################################################### GPF  ##################################################

class EmployeeProvidentFundDetail(LoginRequiredMixin, CustomTableView):
    template_name = 'employee/employee/detail_list.html'
    actions = [{'url': 'employee-gpf-monthly-subscription-detail', 'icon': 'glyphicon glyphicon-th-large',
                'tooltip': 'Detail'}, ]
    model = MonthlyLogForGPF
    title = 'GPF Montly Subscription Logs '

    exclude = ['id', 'provident_fund_profile']
    filter_fields = {'salary_sheet__date': ['exact'],}

    def get(self, request, *args, **kwargs):
        user = self.request.user
        employee = Employee.objects.get(user_ptr=user)
        self.provident_fund_profile = employee.providentfundprofile
        return super().get(request, args, kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        return qs.filter(provident_fund_profile=self.provident_fund_profile, salary_sheet__is_freezed=True)


class EmployeeProvidentFundMonthlySubscriptionDetail(LoginRequiredMixin, DetailView):
    model = MonthlyLogForGPF

    def get(self, request, *args, **kwargs):
        monthly_subscripion = self.get_object()
        salary_sheet = monthly_subscripion.salary_sheet
        return redirect('employee-salary-sheet-detail', pk=salary_sheet.pk)


class EmployeeProvidentFundAdvanceList(LoginRequiredMixin, CustomTableView):
    template_name = 'employee/employee/detail_list.html'

    model = GPFAdvance

    exclude = ['closing_date', 'provident_fund_profile', 'created_at', 'modified_at']

    title = 'General ProvidentFund Advance List'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        employee = Employee.objects.get(user_ptr=user)
        self.provident_fund_profile = employee.providentfundprofile
        return super().get(request, args, kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        return qs.filter(provident_fund_profile=self.provident_fund_profile)

    actions = [
        {'url': 'employee-gpf-advance-detail', 'icon': 'glyphicon glyphicon-th-large', 'tooltip': 'View Detail'}]


class EmployeeGPFAdvanceInstalmentDetail(LoginRequiredMixin, DetailView):
    model = GPFAdvanceInstallment

    def get(self, request, *args, **kwargs):
        monthly_subscripion = self.get_object()
        salary_sheet = monthly_subscripion.salary_sheet
        return redirect('employee-salary-sheet-detail', pk=salary_sheet.pk)


class EmployeeProvidentFundAdvanceDetail(LoginRequiredMixin, ProvidentFundAdvanceDetail):
    template_name = 'employee/employee/providentFund/advance_detail.html'

    actions = [{'url': 'employee-gpf-advance-instalment-detail', 'icon': 'glyphicon glyphicon-th-large',
                'tooltip': 'View Details'}]

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        return qs.filter(gpf_advance=self.gpf_advance, salary_sheet__is_freezed=True)


from django.views.generic.base import View
from wkhtmltopdf.views import PDFTemplateResponse


class MyPDFView(View):
    template = 'template.html'
    context = {'title': 'Hello World!'}

    def get(self, request):
        response = PDFTemplateResponse(request=request,
                                       template=self.template,
                                       filename="hello.pdf",
                                       context=self.context,
                                       show_content_in_browser=False,
                                       cmd_options={'margin-top': 50,},
                                       )
        return response
