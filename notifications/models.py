from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

User = get_user_model()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    receiver_id = models.IntegerField(null=True, blank=True)
    receiver_role = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.message
