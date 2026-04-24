from django.urls import path

from .views import CompanyPaymentsView, MarkPaymentPaidView, WorkerPaymentsView

urlpatterns = [
    path("worker/", WorkerPaymentsView.as_view()),
    path("company/", CompanyPaymentsView.as_view()),
    path("mark-paid/<int:payment_id>/", MarkPaymentPaidView.as_view()),
]
