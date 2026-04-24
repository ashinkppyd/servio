import random
from datetime import timedelta

from django.core.mail import send_mail
from django.utils import timezone

from .models import OTP


def send_otp(email):
    last_otp = OTP.objects.filter(email=email).order_by("-created_at").first()

    if last_otp:
        if (timezone.now() - last_otp.created_at).seconds < 30:
            raise Exception("Wait before requesting another OTP")

    otp = str(random.randint(1000, 9999))
    OTP.objects.filter(email=email).delete()
    OTP.objects.create(
        email=email, otp=otp, expires_at=timezone.now() + timedelta(minutes=1)
    )
    send_mail(
        "Your OTP Code",
        f"Your OTP is {otp}. It will expire in 1 minute.",
        "ashinkppyd@gmail.com",
        [email],
        fail_silently=False,
    )
    return otp
