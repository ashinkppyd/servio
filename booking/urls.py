from django.urls import path

from .views import (
    AddRatingView,
    ApplyBookingView,
    BookingUpdateView,
    CompanyBookingsView,
    MarkAttendanceView,
    UpdateBookingStatusView,
)

urlpatterns = [
    path("apply/", ApplyBookingView.as_view()),
    path("update/<int:booking_id>/", UpdateBookingStatusView.as_view()),
    path("company-bookings/", CompanyBookingsView.as_view()),
    path("attendance/<int:booking_id>/", MarkAttendanceView.as_view()),
    path("rate/<int:booking_id>/", AddRatingView.as_view()),
    path("booking-update/<int:id>/", BookingUpdateView.as_view()),
]
