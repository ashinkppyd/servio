# chat/middleware.py

from asgiref.sync import sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        print(" HEADERS:", headers)
        scope["user"] = AnonymousUser()
        cookie_header = headers.get(b"cookie", b"").decode()
        print("RAW HEADER:", cookie_header)

        token = None

        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith("access_token"):
                token = part.split("=", 1)[1]
                break
        print(" TOKEN:", token)

        if token:
            try:
                access = AccessToken(token)
                user = await get_user(access["user_id"])
                scope["user"] = user
                print(" AUTH USER:", user)
            except Exception as e:
                print("JWT ERROR:", e)
        return await self.inner(scope, receive, send)
