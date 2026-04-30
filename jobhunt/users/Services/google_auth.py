import base64
import json
import os
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone


GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_GMAIL_SEND_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GOOGLE_TOKEN_REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"


@dataclass(slots=True)
class GoogleOAuthTokens:
    access_token: str
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None
    id_token: Optional[str] = None


class GoogleOAuthService:
    """Encapsulates Google OAuth and Gmail API operations."""

    def __init__(self) -> None:
        self.client_id = getattr(settings, "GOOGLE_CLIENT_ID", os.getenv("GOOGLE_CLIENT_ID"))
        self.client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", os.getenv("GOOGLE_CLIENT_SECRET"))
        self.redirect_uri = getattr(settings, "GOOGLE_REDIRECT_URI", os.getenv("GOOGLE_REDIRECT_URI"))

        if not self.client_id or not self.client_secret or not self.redirect_uri:
            raise ValueError(
                "Google OAuth settings are missing. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI."
            )

    def get_login_url(self, state: Optional[str] = None, include_gmail_scope: bool = True) -> str:
        scopes = ["openid", "email", "profile"]
        if include_gmail_scope:
            scopes.append("https://www.googleapis.com/auth/gmail.send")

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
        }
        if state:
            params["state"] = state

        return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str) -> GoogleOAuthTokens:
        payload = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(GOOGLE_TOKEN_ENDPOINT, data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return GoogleOAuthTokens(
            access_token=data["access_token"],
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
            token_type=data.get("token_type"),
            id_token=data.get("id_token"),
        )

    def refresh_access_token(self, refresh_token: str) -> GoogleOAuthTokens:
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        response = requests.post(GOOGLE_TOKEN_ENDPOINT, data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return GoogleOAuthTokens(
            access_token=data["access_token"],
            expires_in=data.get("expires_in"),
            refresh_token=refresh_token,
            scope=data.get("scope"),
            token_type=data.get("token_type"),
            id_token=data.get("id_token"),
        )

    def fetch_user_info(self, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(GOOGLE_USERINFO_ENDPOINT, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def build_user_payload(self, google_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "google_id": google_profile.get("sub"),
            "email": google_profile.get("email"),
            "first_name": google_profile.get("given_name", ""),
            "last_name": google_profile.get("family_name", ""),
            "full_name": google_profile.get("name", ""),
            "avatar_url": google_profile.get("picture", ""),
            "email_verified": google_profile.get("email_verified", False),
        }

    def send_email(
        self,
        access_token: str,
        to_email: str,
        subject: str,
        message_body: str,
        from_email: Optional[str] = None,
        cc_email: Optional[str] = None,
        bcc_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        mime_message = MIMEText(message_body)
        mime_message["to"] = to_email
        mime_message["subject"] = subject

        if from_email:
            mime_message["from"] = from_email
        if cc_email:
            mime_message["cc"] = cc_email
        if bcc_email:
            mime_message["bcc"] = bcc_email

        raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")
        payload = {"raw": raw_message}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            GOOGLE_GMAIL_SEND_ENDPOINT,
            headers=headers,
            data=json.dumps(payload),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def revoke_token(self, token: str) -> None:
        response = requests.post(
            GOOGLE_TOKEN_REVOKE_ENDPOINT,
            params={"token": token},
            timeout=30,
        )
        response.raise_for_status()

    def is_token_expired(self, expires_at) -> bool:
        if not expires_at:
            return True
        return timezone.now() >= expires_at
