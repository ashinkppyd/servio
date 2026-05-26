from django.urls import path

from .views import (
    AddRatingView,
    ApplyBookingView,
    ApplyWaitlistView,
    BookingUpdateView,
    CompanyBookingsView,
    CompanyWaitlistView,
    MarkAttendanceView,
    UpdateBookingStatusView,
    UpdateWaitlistStatusView,
)

urlpatterns = [
    path("apply/", ApplyBookingView.as_view()),
    path("waitlist/apply/", ApplyWaitlistView.as_view()),
    path("waitlist/company/", CompanyWaitlistView.as_view()),
    path("waitlist/update/<int:waitlist_id>/", UpdateWaitlistStatusView.as_view()),
    path("update/<int:booking_id>/", UpdateBookingStatusView.as_view()),
    path("company-bookings/", CompanyBookingsView.as_view()),
    path("attendance/<int:booking_id>/", MarkAttendanceView.as_view()),
    path("rate/<int:booking_id>/", AddRatingView.as_view()),
    path("booking-update/<int:id>/", BookingUpdateView.as_view()),
]
