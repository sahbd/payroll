from django.shortcuts import render, redirect
from django.views.generic import DetailView, DeleteView, View
from django.views.generic.detail import SingleObjectTemplateResponseMixin, BaseDetailView

from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from .forms import SalarySheetDetailsForm, SalarySheetForm
from .calculations import SalarySheetCalculations

from employee.models import Employee
from .models import SalarySheetDetails, SalarySheet, AllowanceDeductionEmployeeClassValue, EmployeeAllowanceDeduction
from .providentFund import ProvidentFundOperations

from duet_admin.utils import CustomTableView,LoginAndAccountantRequired


class SalarySheetList(CustomTableView):
    model = SalarySheet
    template_name = 'duet_account/list.html'

    fields = ['id', 'date', 'is_freezed', 'is_withdrawn', 'net_allowance', 'net_deduction', 'total_payment']
    filter_fields = {'id': ['icontains'], 'date': ['exact'], }

    title = 'Salary Sheet List'

    actions = [{'url': 'duet_account:salary-sheet-detail', 'icon': 'glyphicon glyphicon-th-large', 'tooltip': 'Detail'},
        {'url': 'duet_account:salary-sheet-update', 'icon': 'glyphicon glyphicon-pencil', 'tooltip': 'Update'},
        {'url': 'duet_account:salary-sheet-confirm', 'icon': 'glyphicon glyphicon-lock', 'tooltip': 'Freeze'},
        {'url': 'duet_account:salary-sheet-delete', 'icon': 'glyphicon glyphicon-trash', 'tooltip': 'Delete'}, ]


class EmployeeSalarySheetList(LoginAndAccountantRequired, SalarySheetList):
    template_name = 'duet_account/employee/detail_list.html'

    exclude = ['comment', 'employee']
    filter_fields = {'date': ['exact']}

    def get(self, request, *args, **kwargs):
        self.employee = Employee.objects.get(slug=kwargs.pop('slug'))
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


class SalarySheetCreate(LoginAndAccountantRequired, View):
    def createFormset(self, request, allowance_deductions, prefix, employee):
        formset = []
        employee_class = employee.employee_class
        allowance_deduction_employee_class_values = AllowanceDeductionEmployeeClassValue.objects.filter(
            employee_class=employee_class)

        ## loop employee's applicable allowancesDeductions
        for a in allowance_deductions:
            initial = {'amount': 0}
            allowance_deduction = a.allowance_deduction
            code = allowance_deduction.code
            is_percentage = allowance_deduction.is_percentage

            if code == 'gpf':
                forms = ProvidentFundOperations.create_formset(request, employee, self.employee_basic_pay,
                                                               self.employee_personal_pay)
                formset = formset + forms
            else:
                if a.value:
                    initial['amount'] = SalarySheetCalculations.calculate_default_values(self.employee_basic_pay,
                                                                                         self.employee_personal_pay,
                                                                                         a.value,
                                                                                         is_percentage)
                else:
                    try:
                        allowance_deduction_class_value = allowance_deduction_employee_class_values.get(
                            allowance_deduction=allowance_deduction)
                        initial['amount'] = SalarySheetCalculations.calculate_default_values(self.employee_basic_pay,
                                                                                             self.employee_personal_pay,
                                                                                             allowance_deduction_class_value.value, is_percentage)
                    except AllowanceDeductionEmployeeClassValue.DoesNotExist:
                        pass
                form = SalarySheetDetailsForm(request.POST or None, prefix=prefix + str(a.id),
                                              instance=SalarySheetDetails(), allowance_deduction=allowance_deduction,
                                              initial=initial)
                formset.append(form)
        return formset

    def get(self, request, slug):
        employee = Employee.objects.get(slug=slug)

        employee_allowance_deductions = SalarySheetOperations.get_employee_allowance_deductions(employee)
        allowances = SalarySheetOperations.get_employee_applicable_allowances(employee_allowance_deductions)
        deductions = SalarySheetOperations.get_employee_applicable_deductions(employee_allowance_deductions)

        if SalarySheetOperations.check_employee_allowance_deduction_configurations(request,
                                                                                employee_allowance_deductions) is False:
            return redirect('duet_account:employee-detail', slug=employee.slug)

        self.employee_basic_pay = SalarySheetOperations.get_employee_basic_pay(employee_allowance_deductions)
        self.employee_personal_pay = SalarySheetOperations.get_employee_personal_pay(employee_allowance_deductions)

        allowance_formset = self.createFormset(request, allowances, 'allowance-', employee)
        deduction_formset = self.createFormset(request, deductions, 'deduction-', employee)
        salarySheetForm = SalarySheetForm(instance=SalarySheet())

        return render(request, 'duet_account/employee/salarySheet/generate_salary_sheet.html',
                      {'salary_sheet_form': salarySheetForm, 'employee': employee,
                       'allowanace_formset': allowance_formset, 'deduction_formset': deduction_formset})

    def post(self, request, slug):
        employee = Employee.objects.get(slug=slug)

        employee_allowance_deductions = SalarySheetOperations.get_employee_allowance_deductions(employee)
        allowances = SalarySheetOperations.get_employee_applicable_allowances(employee_allowance_deductions)
        deductions = SalarySheetOperations.get_employee_applicable_deductions(employee_allowance_deductions)
        if SalarySheetOperations.check_employee_allowance_deduction_configurations(request,
                                                                                employee_allowance_deductions) is False:
            return redirect('duet_account:employee-detail', slug=employee.slug)

        self.employee_basic_pay = SalarySheetOperations.get_employee_basic_pay(employee_allowance_deductions)
        self.employee_personal_pay = SalarySheetOperations.get_employee_personal_pay(employee_allowance_deductions)
        allowance_formset = self.createFormset(request, allowances, 'allowance-', employee)
        deduction_formset = self.createFormset(request, deductions, 'deduction-', employee)

        salary_sheet_form = SalarySheetForm(request.POST, instance=SalarySheet())

        formset = allowance_formset + deduction_formset

        if salary_sheet_form.is_valid():
            salary_sheet = salary_sheet_form.save(commit=False)
            salary_sheet.employee = employee
            salary_sheet.save()
            for form in formset:
                instance = form.save(commit=False, salary_sheet=salary_sheet)
                instance.save()
            return redirect('duet_account:employee-detail', slug=employee.slug)
        return render(request, 'duet_account/employee/salarySheet/generate_salary_sheet.html',
                      {'salary_sheet_form': salary_sheet_form, 'employee': employee,
                       'allowanace_formset': allowance_formset, 'deduction_formset': deduction_formset})


class SalarySheetUpdate(LoginAndAccountantRequired, View):
    def create_formset(self, request, allowance_deductions, prefix, employee):
        formset = []
        for a in allowance_deductions:
            initial = {'amount': a.amount}
            form = SalarySheetDetailsForm(request.POST or None, prefix=prefix + str(a.id), instance=a,
                                          allowance_deduction=a.allowance_deduction, initial=initial)
            formset.append(form)
        return formset

    def get(self, request, pk):
        salary_sheet = SalarySheet.objects.get(pk=pk)
        employee = salary_sheet.employee
        if salary_sheet.is_freezed:
            return render(request,
                          'duet_account/employee/update_not_allowed.html', {'employee': employee})

        salary_sheet_details = SalarySheetDetails.objects.filter(salary_sheet=salary_sheet)
        allowances = salary_sheet_details.exclude(allowance_deduction__category='d')
        deductions = salary_sheet_details.filter(allowance_deduction__category='d')

        gpf_formset = ProvidentFundOperations.update_formset(request, salary_sheet)
        allowanace_formset = self.create_formset(request, allowances, 'allowance-', employee)
        deduction_formset = self.create_formset(request, deductions, 'deduction-', employee)

        deduction_formset = gpf_formset + deduction_formset

        salary_sheet_form = SalarySheetForm(instance=salary_sheet)
        return render(request, 'duet_account/employee/salarySheet/generate_salary_sheet.html',
                      {'salary_sheet_form': salary_sheet_form, 'employee': employee,
                       'allowanace_formset': allowanace_formset, 'deduction_formset': deduction_formset})

    def post(self, request, pk):
        salary_sheet = SalarySheet.objects.get(pk=pk)
        employee = salary_sheet.employee
        salary_sheet_details = SalarySheetDetails.objects.filter(salary_sheet=salary_sheet)

        gpf_formset = ProvidentFundOperations.update_formset(request, salary_sheet)
        allowances = salary_sheet_details.exclude(allowance_deduction__category='d')
        deductions = salary_sheet_details.filter(allowance_deduction__category='d')

        allowance_formset = self.create_formset(request, allowances, 'allowance-', employee)
        deduction_formset = gpf_formset + self.create_formset(request, deductions, 'deduction-', employee)

        formset = allowance_formset + deduction_formset

        salary_sheet_form = SalarySheetForm(request.POST, instance=salary_sheet)

        if salary_sheet_form.is_valid():
            salary_sheet_form.save()
            for form in formset:
                instance = form.save(salary_sheet=salary_sheet)
            return redirect('duet_account:employee-detail', slug=employee.slug)
        return render(request, 'duet_account/employee/salarySheet/generate_salary_sheet.html',
                      {'salary_sheet_form': salary_sheet_form, 'employee': employee,
                       'allowanace_formset': allowance_formset, 'deduction_formset': deduction_formset})


class SalarySheetDetail(DetailView):
    model = SalarySheet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        salary_sheet = self.object
        salary_sheet_details = SalarySheetDetails.objects.filter(salary_sheet=salary_sheet)
        allowances = salary_sheet_details.exclude(allowance_deduction__category='d')
        deductions = salary_sheet_details.filter(allowance_deduction__category='d')
        gpf_details = ProvidentFundOperations.get_gpf_deductions(salary_sheet)
        context['allowances'] = allowances
        context['deductions'] = deductions
        context['gpf_details'] = gpf_details
        employee = salary_sheet.employee
        context['employee'] = employee
        context['employee_grade'] = employee.grade
        return context


class AccountSalarySheetDetail(LoginAndAccountantRequired, SalarySheetDetail):
    template_name = 'duet_account/employee/salarySheet/detail.html'




class SalarySheetDelete(LoginAndAccountantRequired, DeleteView):
    model = SalarySheet
    template_name = 'duet_account/employee/confirm_delete.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.employee = self.object.employee
        if self.object.is_freezed:
            return render(request,
                          'duet_account/employee/update_not_allowed.html',
                          {'employee': self.employee})
        request.session['employee_slug'] = self.employee.slug
        return super().get(request, args, kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context

    def post(self, request, *args, **kwargs):
        employee_slug = request.session['employee_slug']
        del request.session['employee_slug']
        self.success_url = reverse_lazy('duet_account:employee-detail', kwargs={'slug': employee_slug})
        return super().post(request, args, kwargs)


class SalarySheetConfirm(LoginAndAccountantRequired, SingleObjectTemplateResponseMixin, BaseDetailView):
    model = SalarySheet
    template_name = 'duet_account/employee/salarySheet/confirm.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.employee = self.object.employee
        if self.object.is_freezed:
            return render(request,
                          'duet_account/employee/update_not_allowed.html',
                          {'employee': self.employee})
        return super().get(request, args, kwargs)

    def post(self, *args, **kwargs):
        salary_sheet = self.get_object()
        salary_sheet.is_freezed = True
        salary_sheet.save()
        return redirect('duet_account:employee-detail', slug=salary_sheet.employee.slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context


class SalarySheetOperations:
    @staticmethod
    def get_employee_allowance_deductions(employee):
        return EmployeeAllowanceDeduction.objects.filter(employee=employee)

    @staticmethod
    def get_employee_applicable_allowances(allowance_deductions):
        return allowance_deductions.filter(is_applicable=True,allowance_deduction__is_applicable=True).exclude(
            allowance_deduction__category='d')

    @staticmethod
    def get_employee_applicable_deductions( allowance_deductions):
        return allowance_deductions.filter(allowance_deduction__category='d', is_applicable=True,
                                           allowance_deduction__is_applicable=True)

    @staticmethod
    def get_employee_basic_pay(allowance_deductions):
        return allowance_deductions.get(allowance_deduction__code='bp').value

    @staticmethod
    def get_employee_personal_pay(allowance_deductions):
        return allowance_deductions.get(allowance_deduction__code='pp').value

    @staticmethod
    def check_employee_allowance_deduction_configurations(request, allowance_deductions):
        def send_message():
            messages.error(request, "Basic Pay/Personal Pay Not Defined")
        try:
            basic_pay = allowance_deductions.get(allowance_deduction__code='bp')
            if basic_pay.value is None:
                send_message()
                return False
        except EmployeeAllowanceDeduction.DoesNotExist:
            send_message()
            return False
        try:
            personal_pay = allowance_deductions.get(allowance_deduction__code='pp')
            if personal_pay is None:
                send_message()
                return False
        except EmployeeAllowanceDeduction.DoesNotExist:
            send_message()
            return False

        return True







