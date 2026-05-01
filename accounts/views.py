import base64
import json
from io import BytesIO

import pyotp
import qrcode
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTP
from .serializers import (
    CompanyRegisterSerializer,
    ProfileSerializer,
    WorkerRegisterSerializer,
)
from .utils import send_otp

User = get_user_model()


class WorkerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WorkerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Worker registered"})
        return Response(serializer.errors, status=400)


class CompanyRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CompanyRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Company registered"})
        return Response(serializer.errors, status=400)


User = get_user_model()


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        # role = request.data.get("role")
        if not email:
            return Response({"error": "Email required"}, status=400)
        response = Response({"message": "OTP sent successfully"}, status=200)

        response.set_cookie(
            key="register_data",
            value=json.dumps(request.data),
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
            max_age=300,
        )
        send_otp(email)
        return response


class VerifyOTPAndRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otp = request.data.get("otp")
        raw_data = request.COOKIES.get("register_data")
        if not raw_data:
            return Response({"error": "Session expired"}, status=400)

        data = json.loads(raw_data)
        email = data.get("email")
        role = data.get("role")
        otp_obj = OTP.objects.filter(email=email).order_by("-created_at").first()

        if not otp_obj:
            return Response({"error": "OTP not found"}, status=400)
        if otp_obj.is_expired():
            return Response({"error": "OTP expired"}, status=400)
        if str(otp_obj.otp) != str(otp):
            return Response({"error": "Invalid OTP"}, status=400)
        otp_obj.delete()

        if role == "worker":
            serializer = WorkerRegisterSerializer(data=data)
        elif role == "company":
            serializer = CompanyRegisterSerializer(data=data)
        else:
            return Response({"error": "Invalid role"}, status=400)

        if serializer.is_valid():
            serializer.save()
            response = Response({"message": f"{role} registered successfully"})
            response.delete_cookie("register_data", path="/")
            return response
        return Response(serializer.errors, status=400)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw_data = request.COOKIES.get("register_data")
        if not raw_data:
            return Response({"error": "Session expired"}, status=400)

        data = json.loads(raw_data)
        email = data.get("email")

        if not email:
            return Response({"error": "Email not found"}, status=400)
        otp_obj = OTP.objects.filter(email=email).order_by("-created_at").first()

        if otp_obj and not otp_obj.can_resend():
            return Response(
                {"error": "Wait 30 seconds before requesting new OTP"}, status=400
            )

        OTP.objects.filter(email=email).delete()
        send_otp(email)
        return Response({"message": "OTP resent successfully"}, status=200)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"error": "Username and password required"}, status=400)
        user = authenticate(request, username=username, password=password)

        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(
                    request, username=user_obj.username, password=password
                )
            except User.DoesNotExist:
                user = None
        if user is None:
            return Response({"error": "Invalid credentials"}, status=401)

        if user.is_mfa_enabled:
            request.session["mfa_user_id"] = user.id
            request.session.modified = True
            return Response({"mfa_required": True, "message": "Enter MFA code"})

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
            }
        )

        response.set_cookie(
            "access_token",
            str(refresh.access_token),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=3600,
            path="/",
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=86400,
            path="/",
        )
        return response


class VerifyLoginMFAView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otp = request.data.get("otp")
        user_id = request.session.get("mfa_user_id")
        if not user_id:
            return Response({"error": "Session expired"}, status=400)

        user = User.objects.get(id=user_id)
        totp = pyotp.TOTP(user.mfa_secret)

        if not totp.verify(otp, valid_window=1):
            return Response({"error": "Invalid OTP"}, status=400)

        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
            }
        )

        response.set_cookie(
            "access_token",
            str(refresh.access_token),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=3600,
            path="/",
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=86400,
            path="/",
        )
        return response


class EnableMFAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.mfa_secret:
            user.mfa_secret = pyotp.random_base32()
            user.save()

        secret = user.mfa_secret
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user.email, issuer_name="SERVIO")

        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        return Response({"qr_code": f"data:image/png;base64,{qr_base64}"})


class VerifyMFAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        otp = request.data.get("otp")
        user = request.user

        if not user.mfa_secret:
            return Response({"error": "MFA not initialized"}, status=400)

        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(otp, valid_window=1):
            user.is_mfa_enabled = True
            user.save()

            return Response({"message": "MFA enabled successfully"})
        return Response({"error": "Invalid code"}, status=400)


class DisableMFAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_mfa_enabled = False
        user.mfa_secret = None
        user.save()

        return Response({"message": "MFA disabled successfully"}, status=200)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("credential")

        if not token:
            return Response({"error": "Token required"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                (
                    "439470469308-jogdufc2e60kcbp02vdctdfdbbd9iu49"
                    ".apps.googleusercontent.com"
                ),
            )
            email = idinfo.get("email")
            if not email:
                return Response({"error": "Email not found"}, status=400)

            user, _ = User.objects.get_or_create(
                email=email, defaults={"username": email, "role": "worker"}
            )
            refresh = RefreshToken.for_user(user)

            response = Response(
                {
                    "message": "Google login success",
                    "user": {
                        "email": user.email,
                        "username": user.username,
                        "role": user.role,
                    },
                }
            )

            response.set_cookie(
                "access_token",
                str(refresh.access_token),
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=3600,
                path="/",
            )
            response.set_cookie(
                "refresh_token",
                str(refresh),
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=86400,
                path="/",
            )
            return response

        except Exception as e:
            print("GOOGLE ERROR:", str(e))
            return Response({"error": "Invalid Google token"}, status=400)


class SaveFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        print("Saving FCM token for user:", request.user.username)

        User.objects.update_or_create(id=request.user.id, defaults={"fcm_token": token})

        return Response(
            {"message": "Token saved successfully"}, status=status.HTTP_200_OK
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "sqs": "triggered",
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"message": "Logged out"})
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.id))
        token = default_token_generator.make_token(user)

        reset_url = f"http://127.0.0.1:5173/reset-password/{uid}/{token}/"

        send_mail(
            "Reset Your Password",
            f"Click the link:\n{reset_url}",
            "ashinkppyd@gmail.com",
            [email],
        )
        return Response({"message": "Reset link sent"}, status=200)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        password = request.data.get("password")

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(id=user_id)
        except Exception:
            return Response({"error": "Invalid link"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid token"}, status=400)

        user.set_password(password)
        user.save()
        return Response({"message": "Password reset successful"}, status=200)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = ProfileSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
