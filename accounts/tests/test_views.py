from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import OTP

User = get_user_model()


class SendOTPViewTest(APITestCase):

    @patch("accounts.views.send_otp")
    def test_send_otp_success(self, mock_send_otp):
        url = "/api/send-otp/"

        data = {"email": "test@test.com", "role": "worker"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)
        mock_send_otp.assert_called_once_with("test@test.com")

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
            '"username":"u1","password":"Pass123!",'
            '"confirm_password":"Pass123!",'
            '"phone":"9876543210",'
            '"state":"Kerala","district":"Kozhikode","place":"City"}'
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
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_login_success_with_email(self):
        url = "/api/login/"

        response = self.client.post(
            url,
            {"username": "ashin@test.com", "password": "test123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["email"], "ashin@test.com")

    def test_login_fail(self):
        url = "/api/login/"

        response = self.client.post(
            url,
            {"username": "ashin", "password": "wrong"},
        )

        self.assertEqual(response.status_code, 401)

    def test_login_requires_username_and_password(self):
        response = self.client.post("/api/login/", {})

        self.assertEqual(response.status_code, 400)


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


class LogoutViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="logout-user",
            email="logout@test.com",
            password="test123",
            role="worker",
            phone="9876543210",
        )
        self.client.force_authenticate(user=self.user)

    def test_logout_deletes_auth_cookies(self):
        self.client.cookies["access_token"] = "access"
        self.client.cookies["refresh_token"] = "refresh"

        response = self.client.post("/api/logout/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")


class ProfileViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="profile-user",
            email="profile@test.com",
            password="test123",
            role="worker",
            phone="9876543211",
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_get(self):
        response = self.client.get("/api/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "profile@test.com")

    def test_profile_update(self):
        response = self.client.put("/api/profile/", {"place": "Kochi"})

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.place, "Kochi")
