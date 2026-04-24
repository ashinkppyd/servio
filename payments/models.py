from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.


User = get_user_model()


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
    ]

    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey("booking.Booking", on_delete=models.CASCADE)
    amount = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.worker.username} - ₹{self.amount} - {self.status}"
