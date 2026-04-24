from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


def send_notification(user, message, sender=None):
    notification = Notification.objects.create(
        user=user,
        message=message,
        receiver_id=sender.custom_id if sender else None,
        receiver_role=sender.role if sender else None,
    )

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "message": message,
            "notification_id": notification.id,
            "receiver_id": notification.receiver_id,
            "receiver_role": notification.receiver_role,
        },
    )
