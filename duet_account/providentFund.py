from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse_lazy
from django.db.models import ProtectedError
from datetime import date, datetime

from django.views.generic import DetailView, DeleteView, View
from django.db.models import Sum
from django.views.generic.detail import SingleObjectTemplateResponseMixin, BaseDetailView

from .forms import MonthlyProvidentFundForm, GPFAdvanceInslallmentForm, YearlyLogForGPFFormUpdate, YearlyLogForGPFFormCreate

from employee.models import Employee
from .models import ProvidentFundProfile, MonthlyLogForGPF, GPFAdvance, GPFAdvanceInstallment, YearlyLogForGPF, \
    SalarySheet

from duet_admin.utils import LoginAndAccountantRequired, CustomTableView, CustomUpdateView, CustomCreateView
from .calculations import SalarySheetCalculations


######################################### Provident Fund Profile #########################################


class ProvidentFundProfileUpdate(LoginAndAccountantRequired, CustomUpdateView):
    model = ProvidentFundProfile
    fields = ['has_interest', 'percentage']
    template_name = 'duet_account/employee/detail_form.html'
    title = 'Edit - '

    def get(self, request, *args, **kwargs):
        self.employee = Employee.objects.get(slug=kwargs.pop('slug'))
        self.object = ProvidentFundProfile.objects.get(employee=self.employee)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context

    def post(self, request, *args, **kwargs):
        self.employee = Employee.objects.get(slug=kwargs.pop('slug'))
        self.object = ProvidentFundProfile.objects.get(employee=self.employee)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        employee = self.object.employee
        return redirect('duet_account:provident-fund-profile-detail', slug=employee.slug)


########################################################### GPF Monthly Subscription ##################################################
class ProvidentFundMonthlySubscriptionDetail(LoginAndAccountantRequired, DetailView):
    model = MonthlyLogForGPF

    def get(self, request, *args, **kwargs):
        monthly_subscripion = self.get_object()
        salary_sheet = monthly_subscripion.salary_sheet
        return redirect('duet_account:salary-sheet-detail', pk=salary_sheet.pk)


class ProvidentFundProfileDetail(LoginAndAccountantRequired, CustomTableView):
    model = MonthlyLogForGPF
    title = 'GPF Montly Subscription Logs '
    template_name = 'duet_account/employee/detail_list.html'

    exclude = ['id', 'provident_fund_profile']
    filter_fields = {'salary_sheet__date': ['exact'], }
    actions = [{'url': 'duet_account:gpf-monthly-subscription-detail', 'icon': 'glyphicon glyphicon-th-large',
                'tooltip': 'Detail'}, ]

    def get(self, request, *args, **kwargs):
        self.employee = Employee.objects.get(slug=kwargs.pop('slug'))
        self.provident_fund_profile = ProvidentFundProfile.objects.get(employee=self.employee)
        return super().get(request, args, kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        return qs.filter(provident_fund_profile=self.provident_fund_profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provident_fund_profile'] = self.provident_fund_profile
        context['employee'] = self.employee
        return context


########################################################### GPF Yearly Log ##################################################

class GPFYearlyLogs(LoginAndAccountantRequired, CustomTableView):
    model = YearlyLogForGPF
    title = 'GPF Yearly Logs '
    template_name = 'duet_account/employee/detail_list.html'

    exclude = ['id', 'provident_fund_profile', 'created_at', 'modified_at']
    filter_fields = {'date': ['exact'], }
    actions = [{'url': 'duet_account:gpf-yearly-log-update', 'icon': 'glyphicon glyphicon-pencil',
                'tooltip': 'Update'},
               {'url': 'duet_account:gpf-yearly-log-confirm', 'icon': 'glyphicon glyphicon-lock',
                'tooltip': 'Freeze'},
               {'url': 'duet_account:gpf-yearly-log-delete', 'icon': 'glyphicon glyphicon-trash',
                                       'tooltip': 'Delete'}, ]

    def get(self, request, *args, **kwargs):
        self.employee = Employee.objects.get(slug=kwargs.pop('slug'))
        self.provident_fund_profile = ProvidentFundProfile.objects.get(employee=self.employee)
        return super().get(request, args, kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        return qs.filter(provident_fund_profile=self.provident_fund_profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context


class GPFYearlyLogConfirm(LoginAndAccountantRequired, SingleObjectTemplateResponseMixin, BaseDetailView):
    model = YearlyLogForGPF
    template_name = 'duet_account/employee/providentFund/yearlyLog/confirm.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.employee = self.object.provident_fund_profile.employee
        if self.object.is_freezed:
            return render(request,
                          'duet_account/employee/update_not_allowed.html',
                          {'employee': self.employee})
        return super().get(request, args, kwargs)

    def post(self, *args, **kwargs):
        yearly_log = self.get_object()
        employee = yearly_log.provident_fund_profile.employee
        yearly_log.is_freezed = True
        yearly_log.save()
        return redirect('duet_account:gpf-yearly-log', slug=employee.slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context


class GPFYearlyLogCreate(LoginAndAccountantRequired, View):
    template_name = 'duet_account/employee/providentFund/yearlyLog/create.html'

    def get(self, request, slug):
        employee = Employee.objects.get(slug=slug)
        provident_fund_profile = ProvidentFundProfile.objects.get(employee=employee)
        yearly_log_for_gpf = YearlyLogForGPF()
        details = ProvidentFundOperations.get_gpf_yearly_details(employee, provident_fund_profile)
        summary = details['summary']
        initial = {'net_deduction' : summary['total_deduction'], 'net_interest': summary['total_interest'], \
                                                                                    'total_credit' :
                                                                                        summary['total_credit']}
        form = YearlyLogForGPFFormCreate(None, instance=yearly_log_for_gpf,
                                   provident_fund_profile=provident_fund_profile, initial= initial)
        return render(request, self.template_name, {'employee': employee, 'form': form, 'details': details})

    def post(self, request, slug):
        employee = Employee.objects.get(slug=slug)
        provident_fund_profile = ProvidentFundProfile.objects.get(employee=employee)
        yearly_log_for_gpf = YearlyLogForGPF()
        form = YearlyLogForGPFFormCreate(request.POST, instance=yearly_log_for_gpf,
                                   provident_fund_profile=provident_fund_profile)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
        return redirect('duet_account:gpf-yearly-log', slug=employee.slug)


class GPFYearlyLogUpdate(LoginAndAccountantRequired, View):
    template_name = 'duet_account/employee/providentFund/yearlyLog/create.html'

    def get(self, request, pk):
        yearly_log_for_gpf= YearlyLogForGPF.objects.select_related('provident_fund_profile__employee').get(pk=pk)
        provident_fund_profile = yearly_log_for_gpf.provident_fund_profile
        employee = provident_fund_profile.employee
        if yearly_log_for_gpf.is_freezed:
            return render(request,'duet_account/employee/update_not_allowed.html', {'employee': employee})
        details = ProvidentFundOperations.get_gpf_yearly_details(employee, provident_fund_profile)
        form = YearlyLogForGPFFormUpdate(None, instance=yearly_log_for_gpf)
        return render(request, self.template_name, {'employee': employee, 'form': form, 'details': details})

    def post(self, request, pk):
        yearly_log_for_gpf = YearlyLogForGPF.objects.select_related('provident_fund_profile__employee').get(pk=pk)
        provident_fund_profile = yearly_log_for_gpf.provident_fund_profile
        employee = provident_fund_profile.employee
        form = YearlyLogForGPFFormUpdate(request.POST , instance=yearly_log_for_gpf)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
        return redirect('duet_account:gpf-yearly-log', slug=employee.slug)


class GPFYearlyLogDelete(LoginAndAccountantRequired, DeleteView):
    model = YearlyLogForGPF
    template_name = 'duet_account/employee/confirm_delete.html'

    def get(self, request, *args, **kwargs):
        yearly_log = self.get_object()
        self.employee = yearly_log.provident_fund_profile.employee
        if yearly_log.is_freezed:
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
        self.success_url = reverse_lazy('duet_account:gpf-yearly-log', kwargs={'slug': employee_slug})
        return super().post(request, args, kwargs)


############################################################### GPF Advance ##########################################################

class ProvidentFundAdvanceCreate(LoginAndAccountantRequired, CustomCreateView):
    model = GPFAdvance
    fields = ['date', 'amount', 'no_of_installments', 'monthly_payment']

    template_name = 'duet_account/employee/detail_form.html'
    title = 'Create New Provident Fund Advance'

    def get(self, request, *args, **kwargs):
        self.employee = Employee.objects.get(slug=kwargs.pop('slug'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context

    def post(self, request, *args, **kwargs):
        self.employee = Employee.objects.get(slug=kwargs.pop('slug'))
        self.provident_fund_profile = ProvidentFundProfile.objects.get(employee=self.employee)
        self.object = None
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.provident_fund_profile = self.provident_fund_profile
        self.object.save()
        return redirect('duet_account:gpf-advance-list', slug=self.employee.slug)


class ProvidentFundAdvanceList(LoginAndAccountantRequired, CustomTableView):
    model = GPFAdvance

    exclude = ['closing_date', 'provident_fund_profile', 'created_at', 'modified_at']

    title = 'General ProvidentFund Advance List'
    template_name = 'duet_account/employee/detail_list.html'

    actions = [
        {'url': 'duet_account:gpf-advance-detail', 'icon': 'glyphicon glyphicon-th-large', 'tooltip': 'View Detail'},
        {'url': 'duet_account:gpf-advance-update', 'icon': 'glyphicon glyphicon-pencil', 'tooltip': 'Update'},
        {'url': 'duet_account:gpf-advance-delete', 'icon': 'glyphicon glyphicon-trash', 'tooltip': 'Delete'}]

    filter_fields = {'date': ['gt', 'lt', ], }

    def get(self, request, *args, **kwargs):
        self.employee = Employee.objects.get(slug=kwargs.pop('slug'))
        self.provident_fund_profile = ProvidentFundProfile.objects.get(employee=self.employee)
        return super().get(request, args, kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        return qs.filter(provident_fund_profile=self.provident_fund_profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provident_fund_profile'] = self.provident_fund_profile
        context['employee'] = self.employee
        return context


class ProvidentFundAdvanceUpdate(LoginAndAccountantRequired, CustomUpdateView):
    model = GPFAdvance
    fields = ['date', 'amount', 'no_of_installments', 'monthly_payment', 'is_closed']
    template_name = 'duet_account/employee/detail_form.html'
    title = 'Edit - '

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.employee = self.object.provident_fund_profile.employee
        if self.object.is_closed:
            return render(request, 'duet_account/employee/providentFund/advance_update_not_allowed.html',
                          {'employee': self.employee})
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        employee = self.object.provident_fund_profile.employee
        return redirect('duet_account:gpf-advance-list', slug=employee.slug)


class ProvidentFundAdvanceDetail(CustomTableView):
    model = GPFAdvanceInstallment

    exclude = ['id', 'gpf_advance']
    filter_fields = {'salary_sheet__date': ['exact'], }

    actions = [{'url': 'duet_account:gpf-advance-installment-detail', 'icon': 'glyphicon glyphicon-th-large',
                'tooltip': 'View Details'}]

    title = 'Installment List'

    def get(self, request, *args, **kwargs):
        self.gpf_advance = GPFAdvance.objects.select_related('provident_fund_profile__employee').get(
            pk=kwargs.pop('pk'))
        return super().get(request, args, kwargs)

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        return qs.filter(gpf_advance=self.gpf_advance)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gpf_advance'] = self.gpf_advance
        context['employee'] = self.gpf_advance.provident_fund_profile.employee
        return context


class AccountProvidentFundAdvanceDetail(LoginAndAccountantRequired, ProvidentFundAdvanceDetail):
    template_name = 'duet_account/employee/providentFund/advance_detail.html'



class GPFAdvanceInstalmentDetail(LoginAndAccountantRequired, DetailView):
    model = GPFAdvanceInstallment

    def get(self, request, *args, **kwargs):
        monthly_subscripion = self.get_object()
        salary_sheet = monthly_subscripion.salary_sheet
        return redirect('duet_account:salary-sheet-detail', pk=salary_sheet.pk)


class GPFAdvanceDelete(LoginAndAccountantRequired, DeleteView):
    model = GPFAdvance
    template_name = 'duet_account/employee/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        try:
            super().delete(request, *args, **kwargs)
            return redirect('duet_account:gpf-advance-list', slug=self.employee.slug)
        except ProtectedError:
            return render(request, 'duet_account/employee/protection_error.html', {'employee': self.employee})

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.employee = self.object.provident_fund_profile.employee
        if self.object.is_closed:
            return render(request, 'duet_account/employee/providentFund/advance_update_not_allowed.html',
                          {'employee': self.employee})
        request.session['employee_slug'] = self.employee.slug
        return super().get(request, args, kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context

    def post(self, request, *args, **kwargs):
        employee_slug = request.session['employee_slug']
        self.employee = Employee.objects.get(slug=employee_slug)
        del request.session['employee_slug']
        self.success_url = reverse_lazy('duet_account:gpf-advance-list', kwargs={'slug': employee_slug})
        return super().post(request, args, kwargs)


############################################### GPF Salary Related Operations ###############################################################


class ProvidentFundOperations(object):
    def create_formset(request, employee, basic_pay, personal_pay):
        formset = []
        try:
            provident_fund_profile = ProvidentFundProfile.objects.get(employee=employee)
            deduction = SalarySheetCalculations.calculate_percentage_from_basic(basic_pay, personal_pay,
                                                                                provident_fund_profile.percentage)
            form = MonthlyProvidentFundForm(request.POST or None, prefix='gpf', instance=MonthlyLogForGPF(),
                                            provident_fund_profile=provident_fund_profile,
                                            initial={'deduction': deduction})
            formset.append(form)
            gpf_advances = GPFAdvance.objects.filter(provident_fund_profile=provident_fund_profile, is_closed=False)
            count = 1
            for gpf_advance in gpf_advances:
                installment_no = gpf_advance._get_last_installment_number() + 1;
                initial = {'deduction': gpf_advance.monthly_payment, 'installment_no': installment_no}
                gpf_installment_form = GPFAdvanceInslallmentForm(request.POST or None,
                                                                 prefix='gpf_advance' + str(count),
                                                                 instance=GPFAdvanceInstallment(),
                                                                 gpf_advance=gpf_advance, initial=initial)
                formset.append(gpf_installment_form)
                count = count + 1
            return formset
        except ProvidentFundProfile.DoesNotExist:
            return formset

    def update_formset(request, salary_sheet):
        formset = []
        try:
            monthly_log = MonthlyLogForGPF.objects.get(salary_sheet=salary_sheet)
            form = MonthlyProvidentFundForm(request.POST or None, prefix='gpf', instance=monthly_log)
            formset.append(form)
        except MonthlyLogForGPF.DoesNotExist:
            pass

        gpf_advance_installments = GPFAdvanceInstallment.objects.filter(salary_sheet=salary_sheet)
        for gpf_advance_installment in gpf_advance_installments:
            gpf_installment_form = GPFAdvanceInslallmentForm(request.POST or None,
                                                             prefix='gpf_advance' + str(gpf_advance_installment.id),
                                                             instance=gpf_advance_installment,
                                                             gpf_advance=gpf_advance_installment.gpf_advance)
            formset.append(gpf_installment_form)
        return formset

    def get_gpf_deductions(salary_sheet):
        gpf_details = dict()
        deduction = 0
        try:
            monthly_log = MonthlyLogForGPF.objects.get(salary_sheet=salary_sheet)
            gpf_details['gpf_subscription'] = monthly_log
            deduction = monthly_log.deduction
        except MonthlyLogForGPF.DoesNotExist:
            pass
        gpf_advance_installments = GPFAdvanceInstallment.objects.filter(salary_sheet=salary_sheet)
        gpf_advance_deductions = gpf_advance_installments.aggregate(total=Sum("deduction"))['total']
        if gpf_advance_deductions is None:
            gpf_advance_deductions = 0
        gpf_details['gpf_advance_installments'] = gpf_advance_installments
        gpf_details['total_gpf_deduction'] = gpf_advance_deductions + deduction
        return gpf_details

    def get_gpf_yearly_details(employee, provident_fund_profile):

        def get_summary_config():
            return  {'total_gpf_deduction' : 0,
                   'total_gpf_interest': 0,
                   'total_advance_deduction' : 0,
                   'total_advance_interest': 0,
                   'initial_credit': 0,
                   'initial_credit_interest': 0,
                   'total_excess': 0,
                   'total_deduction': 0,
                   'total_interest': 0,
                   'total_credit': 0}

        def get_date_june_current_year():
            today = datetime.now()
            return today.replace(day=1, month=6)

        def get_date_july_previous_year():
            today = datetime.now()
            previous_year = today.year - 1
            return today.replace(day=1, month=7, year=previous_year)

        def get_gpf_initial_credit(provident_fund_profile, date):
            try:
                previous_gpf_yearly_log = YearlyLogForGPF.objects.get(provident_fund_profile = provident_fund_profile,
                                                                  date = date)
                return previous_gpf_yearly_log.total_credit

            except YearlyLogForGPF.DoesNotExist:
                return 0

        previous_year_july = get_date_july_previous_year()
        current_year_june = get_date_june_current_year()
        summary = get_summary_config()
        entries = list()

        salary_sheets = SalarySheet.objects.filter(date__gte=previous_year_july, date__lte=current_year_june,
                                                   employee=employee
                                                   ).order_by('date')
        gpf_subscription_list = MonthlyLogForGPF.objects.filter(salary_sheet__date__gte=previous_year_july,
                                                       salary_sheet__date__lte=current_year_june,
                                                                provident_fund_profile= provident_fund_profile)
        gpf_advance_installment_list = GPFAdvanceInstallment.objects.filter(salary_sheet__date__gte=previous_year_july,
                                                       salary_sheet__date__lte=current_year_june,
                                                                            gpf_advance__provident_fund_profile=provident_fund_profile)
        gpf_advance_list = GPFAdvance.objects.filter(date__gte=previous_year_july,
                                                     date__lte=current_year_june,
                                                     provident_fund_profile = provident_fund_profile).order_by('date')



        for salary_sheet in salary_sheets:
            entry = dict()
            entry['date'] = salary_sheet.date
            try:
                gpf_subscription = gpf_subscription_list.get(salary_sheet=salary_sheet)
                entry['gpf_subscription'] = gpf_subscription
            except MonthlyLogForGPF.DoesNotExist:
                pass

            gpf_advance_installments = gpf_advance_installment_list.filter(salary_sheet=salary_sheet)
            entry['gpf_advance_installments'] = gpf_advance_installments
            entries.append(entry)

        gpf_advances = list()
        gpf_advance_access = 0
        for gpf_advance in gpf_advance_list:
            advance = dict()
            advance['advance'] = gpf_advance
            advance['excess'] = SalarySheetCalculations.calculate_gpf_interest(gpf_advance.date,
                                                                               gpf_advance.amount)
            gpf_advance_access += advance['excess']
            gpf_advances.append(advance)

        summary['total_excess'] = gpf_advance_access
        total_deduction = gpf_subscription_list.aggregate(total_deduction = Sum('deduction'))['total_deduction']
        if total_deduction is not None:
            summary['total_gpf_deduction'] = total_deduction

        total_interest = gpf_subscription_list.aggregate( total_interest = Sum('interest'))['total_interest']
        if total_interest is not None:
            summary['total_gpf_interest'] = total_interest

        total_advance_deduction = gpf_advance_installment_list.aggregate(total_deduction = Sum('deduction'))['total_deduction']
        if total_advance_deduction is not None:
            summary['total_advance_deduction'] = total_advance_deduction

        total_advance_interest = gpf_advance_installment_list.aggregate( total_interest = Sum('interest'))['total_interest']
        if total_advance_interest is not None:
            summary['total_advance_interest'] = total_advance_interest

        summary['initial_credit'] = get_gpf_initial_credit(provident_fund_profile, previous_year_july)
        summary['initial_credit_interest'] = SalarySheetCalculations.calculate_gpf_interest_for_year(summary['initial_credit'])
        summary['total_deduction'] = summary['total_gpf_deduction'] + summary['total_advance_deduction']
        summary['total_interest'] = summary['total_gpf_interest'] + summary['total_advance_interest'] + summary['initial_credit_interest']
        summary['total_credit'] = summary['total_deduction'] + summary['total_interest'] + summary['initial_credit'] - summary['total_excess']

        return {'entries' : entries, 'summary' : summary, 'gpf_advances': gpf_advances}
