from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = (
        ("worker", "Worker"),
        ("company", "Company"),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    place = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    custom_id = models.IntegerField(editable=False)
    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)
    is_mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=100, blank=True, null=True)
    role_level = models.CharField(max_length=20, default="catering_boy")
    total_jobs = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.custom_id:
            if self.role == "worker":
                last_user = (
                    User.objects.filter(role="worker").order_by("-custom_id").first()
                )
            else:
                last_user = (
                    User.objects.filter(role="company").order_by("-custom_id").first()
                )
            if last_user and last_user.custom_id:
                self.custom_id = last_user.custom_id + 1
            else:
                self.custom_id = 100
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=1)

    def can_resend(self):
        return timezone.now() > self.created_at + timezone.timedelta(seconds=30)

    def __str__(self):
        return f"{self.email} - {self.otp}"
