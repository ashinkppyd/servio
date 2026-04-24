from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.


User = get_user_model()


class Site(models.Model):
    company = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    date = models.DateField()
    reporting_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Slot(models.Model):
    POSITION_CHOICES = [
        ("juicer", "Juicer"),
        ("juicer_helper", "Juicer Helper"),
        ("catering_boy", "Catering Boy"),
        ("main_boy", "Main Boy"),
        ("supervisor", "Supervisor"),
        ("captain", "Captain"),
        ("chef_helper", "Chef Helper"),
        ("decoration", "Decoration"),
    ]

    site = models.ForeignKey(Site, related_name="slots", on_delete=models.CASCADE)
    position = models.CharField(max_length=50, choices=POSITION_CHOICES)
    total_slots = models.IntegerField()
    available_slots = models.IntegerField(blank=True, null=True)
    salary = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.available_slots is None:
            self.available_slots = self.total_slots
        super().save(*args, **kwargs)

    def filled(self):
        return self.total_slots - self.available_slots

    def total_payout(self):
        return self.filled() * self.salary

    def __str__(self):
        return f"{self.position} - {self.site.name}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey("company.Site", on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1–5
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.site} ({self.rating})"
