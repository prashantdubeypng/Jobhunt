from django.contrib import admin

from .models import (
	ApplicationStatusHistory,
	GoogleIdentity,
	JobApplication,
	OutreachMessage,
	Resume,
	UserPreference,
)


@admin.register(GoogleIdentity)
class GoogleIdentityAdmin(admin.ModelAdmin):
	list_display = ("user", "google_sub", "email_verified", "last_login_at")
	search_fields = ("user__email", "google_sub")
	list_filter = ("email_verified",)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
	list_display = ("user", "auto_apply", "auto_email", "linkedin_outreach", "weekly_digest")
	search_fields = ("user__email",)


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
	list_display = ("user", "title", "is_primary", "created_at")
	search_fields = ("user__email", "title")
	list_filter = ("is_primary",)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
	list_display = ("user", "company_name", "role_title", "source", "status", "applied_at")
	search_fields = ("user__email", "company_name", "role_title")
	list_filter = ("source", "status")


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
	list_display = ("application", "previous_status", "new_status", "created_at")
	search_fields = ("application__company_name",)


@admin.register(OutreachMessage)
class OutreachMessageAdmin(admin.ModelAdmin):
	list_display = ("user", "recipient_name", "channel", "status", "sent_at")
	search_fields = ("user__email", "recipient_name", "recipient_email")
	list_filter = ("channel", "status")
