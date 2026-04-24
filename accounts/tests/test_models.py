from django.test import TestCase
from django.utils import timezone

from accounts.models import OTP, User


class UserModelTest(TestCase):

    def test_create_worker_user(self):
        user = User.objects.create_user(
            username="ashin",
            email="ashin@test.com",
            password="test123",
            role="worker",
            phone="1234567890",
        )

        self.assertEqual(user.role, "worker")
        self.assertTrue(user.check_password("test123"))
        self.assertEqual(user.custom_id, 100)

    def test_custom_id_increment(self):
        u1 = User.objects.create_user(
            username="u1",
            email="u1@test.com",
            password="pass",
            role="worker",
            phone="1111111111",
        )

        u2 = User.objects.create_user(
            username="u2",
            email="u2@test.com",
            password="pass",
            role="worker",
            phone="2222222222",
        )

        self.assertEqual(u2.custom_id, u1.custom_id + 1)

    def test_company_custom_id(self):
        User.objects.create_user(
            username="w",
            email="w@test.com",
            password="pass",
            role="worker",
            phone="9999999999",
        )

        company = User.objects.create_user(
            username="c",
            email="c@test.com",
            password="pass",
            role="company",
            phone="8888888888",
        )

        self.assertEqual(company.custom_id, 100)


class OTPModelTest(TestCase):

    def test_otp_not_expired(self):
        otp = OTP.objects.create(
            email="test@test.com",
            otp="1234",
            expires_at=timezone.now() + timezone.timedelta(minutes=1),
        )
        self.assertFalse(otp.is_expired())

    def test_otp_expired(self):
        otp = OTP.objects.create(
            email="test@test.com",
            otp="1234",
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
        )
        self.assertTrue(otp.is_expired())

    def test_can_resend(self):
        otp = OTP.objects.create(
            email="test@test.com", otp="1234", expires_at=timezone.now()
        )
        self.assertFalse(otp.can_resend())
