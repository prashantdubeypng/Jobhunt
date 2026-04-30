from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    ApplicationStatusHistory,
    GoogleIdentity,
    JobApplication,
    OutreachMessage,
    Resume,
    UserPreference,
)


User = get_user_model()


class GoogleIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleIdentity
        fields = [
            "google_sub",
            "avatar_url",
            "email_verified",
            "token_scope",
            "token_expires_at",
            "last_login_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            "target_job_titles",
            "target_locations",
            "target_companies",
            "target_sources",
            "auto_apply",
            "auto_email",
            "linkedin_outreach",
            "weekly_digest",
            "default_resume",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    google_identity = GoogleIdentitySerializer(read_only=True)
    preference = UserPreferenceSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "google_identity",
            "preference",
        ]
        read_only_fields = fields


class ResumeUploadInitiateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=120, required=False, allow_blank=True)
    file_size = serializers.IntegerField(required=False, min_value=1)
    parsed_text = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    is_primary = serializers.BooleanField(required=False, default=False)


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id",
            "title",
            "file",
            "s3_key",
            "s3_url",
            "original_filename",
            "content_type",
            "file_size",
            "upload_status",
            "uploaded_at",
            "parsed_text",
            "notes",
            "is_primary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "s3_key",
            "s3_url",
            "original_filename",
            "content_type",
            "file_size",
            "upload_status",
            "uploaded_at",
            "created_at",
            "updated_at",
        ]


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationStatusHistory
        fields = [
            "id",
            "previous_status",
            "new_status",
            "note",
            "created_at",
        ]
        read_only_fields = fields


class JobApplicationSerializer(serializers.ModelSerializer):
    resume_title = serializers.CharField(source="resume.title", read_only=True)
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "resume",
            "resume_title",
            "company_name",
            "company_website",
            "role_title",
            "role_location",
            "source",
            "source_url",
            "tracking_url",
            "status",
            "cover_letter",
            "application_payload",
            "response_summary",
            "notes",
            "applied_at",
            "last_status_at",
            "status_history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "last_status_at", "status_history"]


class OutreachMessageSerializer(serializers.ModelSerializer):
    resume_title = serializers.CharField(source="resume.title", read_only=True)
    application_company = serializers.CharField(source="application.company_name", read_only=True)

    class Meta:
        model = OutreachMessage
        fields = [
            "id",
            "application",
            "application_company",
            "resume",
            "resume_title",
            "recipient_name",
            "recipient_email",
            "recipient_linkedin_url",
            "channel",
            "subject",
            "body",
            "provider_message_id",
            "status",
            "sent_at",
            "response_at",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "provider_message_id", "sent_at", "response_at"]
