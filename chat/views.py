from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage
from .serializer import ChatMessageSerializer


class ChatHistoryView(APIView):
    def get(self, request):
        user = request.user
        receiver_id = request.GET.get("receiver_id")
        print(receiver_id, "receiver id")

        messages = ChatMessage.objects.filter(
            Q(sender_id=user.id, receiver_id=receiver_id)
            | Q(sender_id=receiver_id, receiver_id=user.id)
        ).order_by("timestamp")
        print(messages, "hai")

        serializer = ChatMessageSerializer(
            messages, many=True, context={"request": request}
        )
        return Response(serializer.data)


# hello
