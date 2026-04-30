from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from ..models import GoogleIdentity, UserPreference
from .google_auth import GoogleOAuthService, GoogleOAuthTokens
from .token_service import AppTokenService


User = get_user_model()


@dataclass(slots=True)
class GoogleLoginResult:
    user: Any
    google_identity: GoogleIdentity
    preference: UserPreference
    app_token: str
    google_profile: Dict[str, Any]
    google_tokens: GoogleOAuthTokens
    created: bool


class GoogleAuthenticationService:
    def __init__(self, google_service: GoogleOAuthService | None = None, token_service: AppTokenService | None = None) -> None:
        self.google_service = google_service or GoogleOAuthService()
        self.token_service = token_service or AppTokenService()

    @transaction.atomic
    def login_or_create_user(self, code: str) -> GoogleLoginResult:
        google_tokens = self.google_service.exchange_code_for_tokens(code)
        google_profile = self.google_service.fetch_user_info(google_tokens.access_token)
        payload = self.google_service.build_user_payload(google_profile)

        email = payload.get("email")
        google_id = payload.get("google_id")
        if not email or not google_id:
            raise ValueError("Google account did not return the required email or subject identifier.")

        user, created = self._get_or_create_user(payload)
        preference, created_preference = UserPreference.objects.get_or_create(user=user)
        if created_preference or not preference.target_sources:
            preference.target_sources = ["y_combinator", "linkedin"]
            preference.save()
        google_identity = self._upsert_google_identity(user, payload, google_tokens)
        app_token = self.token_service.create_token(user)

        return GoogleLoginResult(
            user=user,
            google_identity=google_identity,
            preference=preference,
            app_token=app_token,
            google_profile=payload,
            google_tokens=google_tokens,
            created=created,
        )

    def _get_or_create_user(self, payload: Dict[str, Any]):
        email = payload["email"]
        first_name = payload.get("first_name", "")
        last_name = payload.get("last_name", "")
        google_id = payload.get("google_id", "")

        username = self._build_unique_username(email=email, google_id=google_id)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        changed = False
        if not user.username:
            user.username = username
            changed = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            changed = True

        user.is_active = True
        user.set_unusable_password()
        if changed or created:
            user.save()
        return user, created

    def _upsert_google_identity(self, user, payload: Dict[str, Any], google_tokens: GoogleOAuthTokens) -> GoogleIdentity:
        expires_at = None
        if google_tokens.expires_in:
            expires_at = timezone.now() + timedelta(seconds=google_tokens.expires_in)

        identity, _ = GoogleIdentity.objects.get_or_create(
            user=user,
            defaults={
                "google_sub": payload["google_id"],
                "avatar_url": payload.get("avatar_url", ""),
                "email_verified": bool(payload.get("email_verified", False)),
                "access_token": google_tokens.access_token,
                "refresh_token": google_tokens.refresh_token or "",
                "token_scope": google_tokens.scope or "",
                "token_expires_at": expires_at,
                "last_login_at": timezone.now(),
            },
        )

        identity.google_sub = payload["google_id"]
        identity.avatar_url = payload.get("avatar_url", "")
        identity.email_verified = bool(payload.get("email_verified", False))
        identity.access_token = google_tokens.access_token
        if google_tokens.refresh_token:
            identity.refresh_token = google_tokens.refresh_token
        if google_tokens.scope:
            identity.token_scope = google_tokens.scope
        identity.token_expires_at = expires_at
        identity.last_login_at = timezone.now()
        identity.save()
        return identity

    def _build_unique_username(self, email: str, google_id: str) -> str:
        base_username = email.split("@")[0].strip().lower() or f"google-{google_id[:8]}"
        candidate = base_username
        index = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base_username}-{index}"
            index += 1
        return candidate
