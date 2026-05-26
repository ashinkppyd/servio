import base64
import json
from io import BytesIO

import pyotp
import qrcode
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
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
        OTP.objects.filter(email=email).delete()
        response = Response({"message": "OTP sent successfully"}, status=200)

        response.set_cookie(
            key="register_data",
            value=json.dumps(request.data),
            httponly=True,
            secure=True,
            samesite="None",
            domain=".servio-events.online",
            path="/",
            max_age=300,
        )
        send_otp(email)
        return response


class VerifyOTPAndRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("VERIFY OTP CALLED WITH DATA:", request.data)

        # Clean OTP input
        otp = str(request.data.get("otp", "")).strip()
        print("OTP RECEIVED:", repr(otp))

        # Get registration data from cookie
        raw_data = request.COOKIES.get("register_data")
        print("RAW DATA FROM COOKIE:", raw_data)

        if not raw_data:
            print("No register_data cookie found")
            return Response({"error": "Session expired"}, status=400)

        try:
            data = json.loads(raw_data)
        except Exception as e:
            print("COOKIE JSON ERROR:", e)
            return Response({"error": "Invalid session data"}, status=400)

        email = data.get("email")
        role = data.get("role")

        print(f"Email: {email}, Role: {role}")

        # Get latest OTP
        otp_obj = OTP.objects.filter(email=email).order_by("-created_at").first()
        print("OTP Object:", otp_obj)

        if not otp_obj:
            return Response({"error": "OTP not found"}, status=400)

        # Debug exact values
        print("DB OTP:", repr(str(otp_obj.otp)))
        print("USER OTP:", repr(otp))
        print("OTP EMAIL:", otp_obj.email)
        print("COOKIE EMAIL:", email)

        # Expiry check
        if otp_obj.is_expired():
            otp_obj.delete()
            return Response({"error": "OTP expired"}, status=400)

        # OTP comparison
        if str(otp_obj.otp).strip() != otp:
            return Response(
                {
                    "error": "Invalid OTP",
                    "db_otp": str(otp_obj.otp),
                    "user_otp": otp,
                },
                status=400,
            )

        # OTP valid
        otp_obj.delete()
        print("OTP verified successfully, proceeding with registration")

        # Registration
        if role == "worker":
            print("Using WorkerRegisterSerializer")
            serializer = WorkerRegisterSerializer(data=data)
            print("Worker serializer initialized with data:", serializer.initial_data)
            print("Worker serializer valid:", serializer.is_valid())
            print("Worker serializer errors:", serializer.errors)

        elif role == "company":
            print("Using CompanyRegisterSerializer")
            serializer = CompanyRegisterSerializer(data=data)
            print("Company serializer valid:", serializer.is_valid())
            print("Company serializer errors:", serializer.errors)

        else:
            print("Invalid role provided:", role)
            return Response({"error": "Invalid role"}, status=400)

        if serializer.is_valid():
            serializer.save()
            print("User registered successfully")

            response = Response(
                {"message": f"{role} registered successfully"}, status=200
            )

            print("Clearing register_data cookie")

            response.delete_cookie(
                key="register_data",
                path="/",
                domain=".servio-events.online",
            )

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
            secure=True,
            samesite="None",
            max_age=3600,
            path="/",
            domain=".servio-events.online",
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=86400,
            path="/",
            domain=".servio-events.online",
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
            secure=True,
            samesite="None",
            max_age=3600,
            path="/",
            domain=".servio-events.online",
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            secure=True,
            samesite="None",
            domain=".servio-events.online",
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
                settings.GOOGLE_CLIENT_ID,
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
                secure=True,
                samesite="None",
                max_age=3600,
                path="/",
                domain=".servio-events.online",
            )
            response.set_cookie(
                "refresh_token",
                str(refresh),
                httponly=True,
                secure=True,
                samesite="None",
                max_age=86400,
                path="/",
                domain=".servio-events.online",
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
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({"message": "Logged out"}, status=200)

        response.delete_cookie(
            key="access_token",
            path="/",
            domain=".servio-events.online",
            samesite="None",
        )

        response.delete_cookie(
            key="refresh_token",
            path="/",
            domain=".servio-events.online",
            samesite="None",
        )

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

        frontend_url = (
            request.headers.get("Origin")
            or getattr(settings, "FRONTEND_URL", "http://127.0.0.1:5173")
        ).rstrip("/")
        reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"

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


# class WorkerDirectoryView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         query = request.GET.get("q", "").strip()
#         workers = User.objects.filter(role="worker", is_active=True).order_by(
#             "username"
#         )

#         if query:
#             workers = workers.filter(
#                 Q(username__icontains=query)
#                 | Q(email__icontains=query)
#                 | Q(phone__icontains=query)
#                 | Q(place__icontains=query)
#                 | Q(district__icontains=query)
#                 | Q(role_level__icontains=query)
#             )

#         data = []
#         for worker in workers:
#             data.append(
#                 {
#                     "id": worker.id,
#                     "username": worker.username,
#                     "email": worker.email,
#                     "phone": worker.phone,
#                     "place": worker.place,
#                     "district": worker.district,
#                     "state": worker.state,
#                     "role_level": worker.role_level,
#                     "total_jobs": worker.total_jobs,
#                     "profile_image": (
#                         worker.profile_image.url if worker.profile_image else None
#                     ),
#                 }
#             )

#         return Response(data)


class WorkerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, worker_id):
        try:
            worker = User.objects.get(id=worker_id, role="worker")
        except User.DoesNotExist:
            return Response({"error": "Worker not found"}, status=404)

        return Response(
            {
                "id": worker.id,
                "username": worker.username,
                "email": worker.email,
                "phone": worker.phone,
                "place": worker.place,
                "district": worker.district,
                "state": worker.state,
                "role_level": worker.role_level,
                "total_jobs": worker.total_jobs,
                "profile_image": (
                    worker.profile_image.url if worker.profile_image else None
                ),
            }
        )


def health_check(request):
    return JsonResponse({"status": "healthy"}, status=200)
