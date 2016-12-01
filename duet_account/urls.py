from django.conf.urls import url
from .views import EmployeeList
from .allowanceDeduction import ConfigureAllowanceDeduction, ConfigureAllowanceDeductionEmployeeClassValue, \
    AllowanceDeductionDetail, AllowanceDeductionList, AllowanceDeductionUpdate, ConfigureEmployeeAllowanceDeduction

from .providentFund import ProvidentFundProfileUpdate, ProvidentFundProfileDetail, GPFYearlyLogs, GPFYearlyLogCreate, \
    ProvidentFundAdvanceList, ProvidentFundMonthlySubscriptionDetail, ProvidentFundAdvanceCreate, \
    ProvidentFundAdvanceUpdate, AccountProvidentFundAdvanceDetail, GPFAdvanceDelete, GPFAdvanceInstalmentDetail, \
    GPFYearlyLogConfirm, GPFYearlyLogDelete, GPFYearlyLogUpdate

from .salarySheet import SalarySheetCreate, SalarySheetUpdate, AccountSalarySheetDetail, SalarySheetConfirm, \
    SalarySheetDelete, EmployeeSalarySheetList

urlpatterns = [
    url(r'^$', EmployeeList.as_view(), name = 'employee-list'),
    url(r'^employees/manageAllowanceDeductions/(?P<slug>[-\w]+)/$', ConfigureEmployeeAllowanceDeduction.as_view(), name = 'configure-employee-allowance-deduction'),
    url(r'^employees/(?P<slug>[-\w]+)/$', EmployeeSalarySheetList.as_view(), name ='employee-detail'),
    url(r'^employees/$', EmployeeList.as_view(), name = 'employee-list'),
   	url(r'^employees/GenerateSalarySheet/(?P<slug>[-\w]+)/$', SalarySheetCreate.as_view(), name = 'generate-salary-sheet'),
    url(r'^employees/providentFund/edit/(?P<slug>[-\w]+)/$', ProvidentFundProfileUpdate.as_view(), name = 'provident-fund-profile-update'),
    url(r'^employees/providentFund/detail/(?P<slug>[-\w]+)/$', ProvidentFundProfileDetail.as_view(), name ='provident-fund-profile-detail'),
    url(r'^employees/providentFund/gpfYearlyLog/(?P<slug>[-\w]+)/$', GPFYearlyLogs.as_view(),
        name ='gpf-yearly-log'),
    url(r'^employees/providentFund/gpfYearlyLog/create/(?P<slug>[-\w]+)/$', GPFYearlyLogCreate.as_view(),
        name ='create-gpf-yearly-log'),
    url(r'^employees/providentFund/gpfYearlyLog/freeze/(?P<pk>\d+)/$', GPFYearlyLogConfirm.as_view(),
        name = 'gpf-yearly-log-confirm'),
    url(r'^employees/providentFund/gpfYearlyLog/delete/(?P<pk>\d+)/$', GPFYearlyLogDelete.as_view(),
        name = 'gpf-yearly-log-delete'),
    url(r'^employees/providentFund/gpfYearlyLog/update/(?P<pk>\d+)/$', GPFYearlyLogUpdate.as_view(),
        name = 'gpf-yearly-log-update'),
    url(r'^employees/providentFund/advances/(?P<slug>[-\w]+)/$', ProvidentFundAdvanceList.as_view(), name = 'gpf-advance-list'),

   	url(r'^salarySheets/update/(?P<pk>\d+)/$', SalarySheetUpdate.as_view(), name = 'salary-sheet-update'),
   	url(r'^salarySheets/delete/(?P<pk>\d+)/$', SalarySheetDelete.as_view(), name = 'salary-sheet-delete'),
   	url(r'^salarySheets/detail/(?P<pk>\d+)/$', AccountSalarySheetDetail.as_view(), name ='salary-sheet-detail'),
    url(r'^salarySheets/freeze/(?P<pk>\d+)/$', SalarySheetConfirm.as_view(), name = 'salary-sheet-confirm'),

   	url(r'^allowanceDeductions/$', AllowanceDeductionList.as_view(), name = 'allowance-deduction-list'),
    url(r'^allowanceDeductions/(?P<slug>[-\w]+)/$', AllowanceDeductionDetail.as_view(), name = 'allowance-deduction-detail'),
   	url(r'^allowanceDeductions/edit/(?P<slug>[-\w]+)/$', AllowanceDeductionUpdate.as_view(), name = 'allowance-deduction-update'),
   	url(r'^allowanceDeductions/ConfigureValuesForEmployeeClass/(?P<slug>[-\w]+)/$', ConfigureAllowanceDeductionEmployeeClassValue.as_view(), name = 'configure-allowance-deduction-employee-class'),
   	url(r'^allowanceDeductions/ConfigureAllowancesDeductions$', ConfigureAllowanceDeduction.as_view(), name = 'configure-allowance-deduction'),

    url(r'^providentFunds/montlySubscriptionLogs/detail/(?P<pk>\d+)/$', ProvidentFundMonthlySubscriptionDetail.as_view(), name = 'gpf-monthly-subscription-detail'),
    
    url(r'^employees/providentFunds/createAdvance/(?P<slug>[-\w]+)/$', ProvidentFundAdvanceCreate.as_view(), name = 'gpf-new-advance'),
    url(r'^providentFunds/advances/edit/(?P<pk>\d+)/$', ProvidentFundAdvanceUpdate.as_view(), name = 'gpf-advance-update'),
    url(r'^providentFunds/advances/detail/(?P<pk>\d+)/$', AccountProvidentFundAdvanceDetail.as_view(), name ='gpf-advance-detail'),
    url(r'^providentFunds/advances/delete/(?P<pk>\d+)/$', GPFAdvanceDelete.as_view(), name = 'gpf-advance-delete'),
    url(r'^providentFunds/advances/installment/detail/(?P<pk>\d+)/$', GPFAdvanceInstalmentDetail.as_view(), name = 'gpf-advance-installment-detail'),

]



