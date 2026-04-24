import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from notifications.utils import send_notification

from .models import ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        print(" CONNECT USER:", self.user)

        if not self.user or self.user.is_anonymous:
            print(" Anonymous user - closing socket")
            await self.close()
            return
        self.room = f"{self.user.role}_{self.user.custom_id}"
        self.notify_room = f"user_{self.user.id}"

        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.channel_layer.group_add(self.notify_room, self.channel_name)
        await self.accept()
        print(f" Connected to room: {self.room}")

    async def disconnect(self, close_code):
        if hasattr(self, "room"):
            await self.channel_layer.group_discard(self.room, self.channel_name)
            await self.channel_layer.group_discard(self.notify_room, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        message = data.get("message")
        receiver_id = data.get("receiver_id")
        receiver_role = data.get("receiver_role")
        temp_id = data.get("temp_id")

        if not message or not receiver_id or not receiver_role:
            print(" Missing data")
            return
        receiver = await self.get_user(receiver_id)

        if not receiver:
            print(" Receiver not found")
            return

        chat = await self.save_message(
            sender=self.user, receiver=receiver, message=message
        )
        await sync_to_async(send_notification)(
            receiver, f"{self.user.username} sent you a message", sender=self.user
        )
        sender_payload = {
            "id": chat.id,
            "message": chat.message,
            "sender_id": self.user.id,
            "sender_name": self.user.username,
            "is_me": True,
            "temp_id": temp_id,
        }

        receiver_payload = {
            "id": chat.id,
            "message": chat.message,
            "sender_id": self.user.id,
            "sender_name": self.user.username,
            "is_me": False,
            "temp_id": temp_id,
        }
        await self.channel_layer.group_send(
            f"{receiver.role}_{receiver.custom_id}",
            {"type": "chat_message", **receiver_payload},
        )
        await self.send(text_data=json.dumps(sender_payload))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def send_notification(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "message": event["message"],
                    "notification_id": event["notification_id"],
                    "receiver_id": event.get("receiver_id"),
                    "receiver_role": event.get("receiver_role"),
                }
            )
        )

    @sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return None

    @sync_to_async
    def save_message(self, sender, receiver, message):
        return ChatMessage.objects.create(
            sender=sender, receiver=receiver, message=message
        )
