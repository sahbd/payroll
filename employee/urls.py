from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^$', EmployeeProfile.as_view(), name='employee-profile'),
    url(r'^profile/edit/$', EmployeeProfileUpdate.as_view(), name='employee-profile-update'),
    url(r'^salaryLists/$', EmployeeSalaryList.as_view(), name='employee-salary-list'),
    url(r'^allowanceDeductions/$', EmployeeAllowanceDeductionList.as_view(), name='employee-allowance-deduction-list'),
    url(r'^employees/salarySheets/detail/(?P<pk>\d+)/$', EmployeeSalarySheetDetail.as_view(), name='employee-salary-sheet-detail'),
    url(r'^gpfMonthlyLogs/$', EmployeeProvidentFundDetail.as_view(), name='employee-gpf-monthly-logs'),
    url(r'^gpfMonthlyLogs/detail/(?P<pk>\d+)$', EmployeeProvidentFundMonthlySubscriptionDetail.as_view(),
        name='employee-gpf-monthly-subscription-detail'),
    url(r'^providentFundAdvances/$', EmployeeProvidentFundAdvanceList.as_view(), name='employee-gpf-advance-list'),
    url(r'^providentFundAdvances/detail/(?P<pk>\d+)/$', EmployeeProvidentFundAdvanceDetail.as_view(),
        name='employee-gpf-advance-detail'),
    url(r'^providentFundAdvances/instalmentDetail/(?P<pk>\d+)$', EmployeeGPFAdvanceInstalmentDetail.as_view(),
        name='employee-gpf-advance-instalment-detail'),
    url(r'^pdf/', MyPDFView.as_view()),
]
