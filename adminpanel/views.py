from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdminUserRole
from .serializers import CompanySerializer, WorkerSerializer

User = get_user_model()


class AdminDashboardView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        total_workers = User.objects.filter(role="worker").count()
        total_companies = User.objects.filter(role="company").count()
        active_workers = User.objects.filter(role="worker", is_active=True).count()
        active_companies = User.objects.filter(role="company", is_active=True).count()

        return Response(
            {
                "total_workers": total_workers,
                "total_companies": total_companies,
                "active_workers": active_workers,
                "active_companies": active_companies,
                "blocked_workers": total_workers - active_workers,
                "blocked_companies": total_companies - active_companies,
            }
        )


class WorkerListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        workers = User.objects.filter(role="worker").order_by("-id")
        serializer = WorkerSerializer(workers, many=True)
        return Response(serializer.data)


class CompanyListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        companies = User.objects.filter(role="company").order_by("-id")
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data)


class BlockUserView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role__in=["worker", "company"])
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"message": "User blocked successfully"})


class UnblockUserView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role__in=["worker", "company"])
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response({"message": "User unblocked successfully"})
