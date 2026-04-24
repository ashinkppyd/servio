from rest_framework import serializers

from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.username", read_only=True)
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ["id", "message", "timestamp", "sender_name", "is_me"]

    def get_is_me(self, obj):
        request = self.context.get("request")
        return obj.sender_id == request.user.id
