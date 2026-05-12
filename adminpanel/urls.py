from django.urls import path

from .views import (
    AdminDashboardView,
    BlockUserView,
    CompanyListView,
    UnblockUserView,
    WorkerListView,
)

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view()),
    path("workers/", WorkerListView.as_view()),
    path("companies/", CompanyListView.as_view()),
    path("block/<int:user_id>/", BlockUserView.as_view()),
    path("unblock/<int:user_id>/", UnblockUserView.as_view()),
]
