from datetime import datetime, timedelta, timezone as datetime_timezone

from django.core import signing
from django.utils import timezone


class AppTokenService:
    salt = "jobhunt.users.app-token"
    default_ttl_minutes = 60 * 24 * 7

    def create_token(self, user, ttl_minutes: int | None = None) -> str:
        expires_at = timezone.now() + timedelta(minutes=ttl_minutes or self.default_ttl_minutes)
        payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": expires_at.timestamp(),
        }
        return signing.dumps(payload, salt=self.salt)

    def decode_token(self, token: str) -> dict:
        payload = signing.loads(token, salt=self.salt)
        expires_at = datetime.fromtimestamp(payload["exp"], tz=datetime_timezone.utc)
        if timezone.now() > expires_at:
            raise signing.SignatureExpired("App token expired")
        return payload