from django.urls import path

from .views import (
    MarkAllNotificationsReadView,
    MarkNotificationReadView,
    UserNotificationsView,
)

urlpatterns = [
    path("notifications/", UserNotificationsView.as_view()),
    path(
        "notifications/read/<int:notification_id>/", MarkNotificationReadView.as_view()
    ),
    path("notifications/read-all/", MarkAllNotificationsReadView.as_view()),
]
