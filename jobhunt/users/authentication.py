from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .Services.token_service import AppTokenService


User = get_user_model()


class AppTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith(f"{self.keyword} "):
            return None

        token = header.split(" ", 1)[1].strip()
        if not token:
            return None

        try:
            payload = AppTokenService().decode_token(token)
        except Exception as exc:  # noqa: BLE001 - converted to DRF auth failure
            raise AuthenticationFailed("Invalid or expired app token.") from exc

        user = User.objects.filter(pk=payload["user_id"], is_active=True).first()
        if not user:
            raise AuthenticationFailed("User not found.")

        return (user, token)