from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.utils import timezone


@dataclass(slots=True)
class PresignedUploadData:
    s3_key: str
    s3_url: str
    presigned_url: str
    expires_in: int


class S3PresignedUploadService:
    def __init__(self, bucket_name: str | None = None, region_name: str | None = None):
        self.bucket_name = bucket_name or getattr(settings, "AWS_S3_BUCKET_NAME", "")
        self.region_name = region_name or getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")
        self.access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID", "")
        self.secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", "")
        self.expires_in = getattr(settings, "AWS_S3_PRESIGNED_TTL_SECONDS", 900)

        if not self.bucket_name:
            raise ValueError("AWS S3 bucket name is missing. Set AWS_S3_BUCKET_NAME.")

        self.client = boto3.client(
            "s3",
            region_name=self.region_name,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "virtual"},
            ),
            aws_access_key_id=self.access_key_id or None,
            aws_secret_access_key=self.secret_access_key or None,
        )

    def build_object_key(self, user_id: int, resume_id: int, filename: str) -> str:
        safe_filename = filename.replace(" ", "_")
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        return f"resumes/{user_id}/{resume_id}/{timestamp}_{uuid4().hex}_{safe_filename}"

    def build_object_url(self, key: str) -> str:
        if self.region_name == "us-east-1":
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"

    def create_presigned_upload(self, *, user_id: int, resume_id: int, filename: str, content_type: str = "application/octet-stream") -> PresignedUploadData:
        s3_key = self.build_object_key(user_id, resume_id, filename)
        presigned_url = self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": s3_key,
                "ContentType": content_type or "application/octet-stream",
            },
            ExpiresIn=self.expires_in,
            HttpMethod="PUT",
        )
        return PresignedUploadData(
            s3_key=s3_key,
            s3_url=self.build_object_url(s3_key),
            presigned_url=presigned_url,
            expires_in=self.expires_in,
        )

    def delete_object(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except (BotoCoreError, ClientError):
            return
