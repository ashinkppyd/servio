from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import OTP

User = get_user_model()


class SendOTPViewTest(APITestCase):

    def test_send_otp_success(self):
        url = "/api/send-otp/"

        data = {"email": "test@test.com", "role": "worker"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)

    def test_send_otp_no_email(self):
        url = "/api/send-otp/"
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, 400)


class VerifyOTPTest(APITestCase):

    def setUp(self):
        self.email = "test@test.com"

        self.otp = OTP.objects.create(
            email=self.email,
            otp="1234",
            expires_at=timezone.now() + timezone.timedelta(minutes=1),
        )

        self.client.cookies["register_data"] = (
            '{"email": "test@test.com", "role": "worker", '
            '"username":"u1","password":"pass123","phone":"1234567890"}'
        )

    def test_verify_otp_success(self):
        url = "/api/verify-otp/"

        response = self.client.post(url, {"otp": "1234"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)

    def test_verify_otp_wrong(self):
        url = "/api/verify-otp/"

        response = self.client.post(url, {"otp": "9999"})

        self.assertEqual(response.status_code, 400)


class LoginViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="ashin",
            email="ashin@test.com",
            password="test123",
            role="worker",
            phone="1234567890",
        )

    def test_login_success(self):
        url = "/api/login/"

        response = self.client.post(
            url,
            {"username": "ashin", "password": "test123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)

    def test_login_fail(self):
        url = "/api/login/"

        response = self.client.post(
            url,
            {"username": "ashin", "password": "wrong"},
        )

        self.assertEqual(response.status_code, 401)


class MeViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="ashin",
            email="ashin@test.com",
            password="test123",
            role="worker",
            phone="1234567890",
        )
        self.client.force_authenticate(user=self.user)

    def test_me(self):
        response = self.client.get("/api/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "ashin@test.com")
