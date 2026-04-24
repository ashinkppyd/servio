from django.urls import path

from .views import WorkerPaymentView, WorkerSiteReportView, WorkerSitesView

urlpatterns = [
    path("sites/", WorkerSitesView.as_view()),
    path("report/", WorkerSiteReportView.as_view()),
    path("payments/", WorkerPaymentView.as_view()),
]
