from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification


class UserNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by(
            "-created_at"
        )

        data = [
            {
                "id": n.id,
                "message": n.message,
                "is_read": n.is_read,
                "time": n.created_at,
                "receiver_id": n.receiver_id,
                "receiver_role": n.receiver_role,
                "user_id": n.user_id,
            }
            for n in notifications
        ]

        return Response(data)


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        try:
            n = Notification.objects.get(id=notification_id, user=request.user)
            n.is_read = True
            n.save()

            return Response({"message": "Marked as read"})
        except Notification.DoesNotExist:
            return Response({"error": "Not found"}, status=404)


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )

        return Response({"message": "All marked as read"})
