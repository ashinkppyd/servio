from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from booking.models import Booking
from notifications.utils import send_notification


@shared_task
def test_task():
    print(" Celery is working!")
    return "Done"


@shared_task
def send_upcoming_work_reminders():
    tomorrow = timezone.localdate() + timedelta(days=1)
    bookings = (
        Booking.objects.select_related(
            "worker", "slot", "slot__site", "slot__site__company"
        )
        .filter(
            status="approved",
            slot__site__date=tomorrow,
            worker__email__isnull=False,
        )
        .exclude(Q(worker__email="") | Q(reminder_sent_at__isnull=False))
    )

    sent_count = 0

    for booking in bookings:
        site = booking.slot.site
        company = site.company
        subject = f"Work reminder for {site.name} on {site.date}"
        message = (
            f"Hello {booking.worker.username},\n\n"
            "This is a reminder that your approved work for "
            f"{company.company_name or company.username} "
            f"is scheduled for tomorrow.\n\n"
            f"Site: {site.name}\n"
            f"Location: {site.location}\n"
            f"Date: {site.date}\n"
            f"Reporting time: {site.reporting_time}\n"
            f"Role: {booking.slot.position}\n\n"
            "Please make sure you report on time."
        )

        send_mail(subject, message, None, [booking.worker.email], fail_silently=False)
        send_notification(
            booking.worker,
            f"Reminder: your approved work at {site.name} is tomorrow.",
        )
        booking.reminder_sent_at = timezone.now()
        booking.save(update_fields=["reminder_sent_at"])
        sent_count += 1

    return f"Sent {sent_count} reminder emails"
