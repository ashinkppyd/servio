from django.contrib.auth import get_user_model
from django.db import models

from company.models import Slot

# Create your models here.


User = get_user_model()


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    ATTENDANCE_CHOICES = [
        ("pending", "Pending"),
        ("present", "Present"),
        ("absent", "Absent"),
    ]

    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    attendance = models.CharField(
        max_length=20, choices=ATTENDANCE_CHOICES, default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["worker", "slot"]


class Rating(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
