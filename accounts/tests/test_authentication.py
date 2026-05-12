from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.authentication import CookieJWTAuthentication

User = get_user_model()


class CookieJWTAuthenticationTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.authenticator = CookieJWTAuthentication()
        self.user = User.objects.create_user(
            username="auth-user",
            email="auth@test.com",
            password="test123",
            role="worker",
            phone="9876543212",
        )

    def test_returns_none_without_header_or_cookie(self):
        request = self.factory.get("/api/me/")

        result = self.authenticator.authenticate(request)

        self.assertIsNone(result)

    def test_authenticates_from_access_token_cookie(self):
        token = RefreshToken.for_user(self.user).access_token
        request = self.factory.get("/api/me/")
        request.COOKIES["access_token"] = str(token)

        user, validated_token = self.authenticator.authenticate(request)

        self.assertEqual(user, self.user)
        self.assertEqual(str(validated_token["user_id"]), str(self.user.id))

    def test_invalid_cookie_token_raises_authentication_failed(self):
        request = self.factory.get("/api/me/")
        request.COOKIES["access_token"] = "bad-token"

        with self.assertRaises(AuthenticationFailed):
            self.authenticator.authenticate(request)
