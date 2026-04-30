from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class GoogleIdentity(TimeStampedModel):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="google_identity",
	)
	google_sub = models.CharField(max_length=255, unique=True, db_index=True)
	avatar_url = models.URLField(blank=True)
	email_verified = models.BooleanField(default=False)
	access_token = models.TextField(blank=True)
	refresh_token = models.TextField(blank=True)
	token_scope = models.TextField(blank=True)
	token_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
	last_login_at = models.DateTimeField(null=True, blank=True, db_index=True)

	def __str__(self) -> str:
		return f"GoogleIdentity<{self.user.email}>"

	class Meta:
		indexes = [
			models.Index(fields=["last_login_at"], name="google_last_login_idx"),
			models.Index(fields=["token_expires_at"], name="google_token_exp_idx"),
		]


class UserPreference(TimeStampedModel):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="preference",
	)
	target_job_titles = models.JSONField(default=list, blank=True)
	target_locations = models.JSONField(default=list, blank=True)
	target_companies = models.JSONField(default=list, blank=True)
	target_sources = models.JSONField(default=list, blank=True)
	auto_apply = models.BooleanField(default=False)
	auto_email = models.BooleanField(default=False)
	linkedin_outreach = models.BooleanField(default=False)
	weekly_digest = models.BooleanField(default=True)
	default_resume = models.ForeignKey(
		"Resume",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="preferred_for",
	)

	def __str__(self) -> str:
		return f"Preferences<{self.user.email}>"


class Resume(TimeStampedModel):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="resumes",
	)
	title = models.CharField(max_length=255)
	file = models.FileField(upload_to="resumes/", blank=True, null=True)
	parsed_text = models.TextField(blank=True)
	notes = models.TextField(blank=True)
	is_primary = models.BooleanField(default=False, db_index=True)

	class Meta:
		ordering = ["-is_primary", "-created_at"]
		indexes = [
			models.Index(fields=["user", "is_primary"], name="resume_user_primary_idx"),
			models.Index(fields=["user", "-created_at"], name="resume_user_created_idx"),
		]

	def __str__(self) -> str:
		return f"Resume<{self.user.email}:{self.title}>"


class JobApplication(TimeStampedModel):
	class Source(models.TextChoices):
		Y_COMBINATOR = "y_combinator", "Y Combinator"
		LINKEDIN = "linkedin", "LinkedIn"
		MANUAL = "manual", "Manual"

	class Status(models.TextChoices):
		DRAFT = "draft", "Draft"
		APPLIED = "applied", "Applied"
		IN_REVIEW = "in_review", "In Review"
		INTERVIEW = "interview", "Interview"
		REJECTED = "rejected", "Rejected"
		OFFER = "offer", "Offer"
		WITHDRAWN = "withdrawn", "Withdrawn"

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="applications",
	)
	resume = models.ForeignKey(
		Resume,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="applications",
	)
	company_name = models.CharField(max_length=255)
	company_website = models.URLField(blank=True)
	role_title = models.CharField(max_length=255)
	role_location = models.CharField(max_length=255, blank=True)
	source = models.CharField(max_length=30, choices=Source.choices, default=Source.MANUAL, db_index=True)
	source_url = models.URLField(blank=True)
	tracking_url = models.URLField(blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
	cover_letter = models.TextField(blank=True)
	application_payload = models.JSONField(default=dict, blank=True)
	response_summary = models.TextField(blank=True)
	notes = models.TextField(blank=True)
	applied_at = models.DateTimeField(null=True, blank=True, db_index=True)
	last_status_at = models.DateTimeField(null=True, blank=True, db_index=True)

	class Meta:
		ordering = ["-last_status_at", "-created_at"]
		indexes = [
			models.Index(fields=["user", "status"], name="jobapp_user_status_idx"),
			models.Index(fields=["user", "-created_at"], name="jobapp_user_created_idx"),
			models.Index(fields=["source", "-created_at"], name="jobapp_source_created_idx"),
			models.Index(fields=["status", "-applied_at"], name="jobapp_status_applied_idx"),
		]

	def __str__(self) -> str:
		return f"Application<{self.user.email}:{self.company_name} - {self.role_title}>"


class ApplicationStatusHistory(TimeStampedModel):
	application = models.ForeignKey(
		JobApplication,
		on_delete=models.CASCADE,
		related_name="status_history",
	)
	previous_status = models.CharField(max_length=20, db_index=True)
	new_status = models.CharField(max_length=20, db_index=True)
	note = models.TextField(blank=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["application", "-created_at"], name="appstatus_app_created_idx"),
		]


class OutreachMessage(TimeStampedModel):
	class Channel(models.TextChoices):
		EMAIL = "email", "Email"
		LINKEDIN = "linkedin", "LinkedIn"

	class Status(models.TextChoices):
		DRAFT = "draft", "Draft"
		QUEUED = "queued", "Queued"
		SENT = "sent", "Sent"
		DELIVERED = "delivered", "Delivered"
		OPENED = "opened", "Opened"
		REPLIED = "replied", "Replied"
		FAILED = "failed", "Failed"

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="outreach_messages",
	)
	application = models.ForeignKey(
		JobApplication,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="outreach_messages",
	)
	resume = models.ForeignKey(
		Resume,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="outreach_messages",
	)
	recipient_name = models.CharField(max_length=255)
	recipient_email = models.EmailField(blank=True, db_index=True)
	recipient_linkedin_url = models.URLField(blank=True)
	channel = models.CharField(max_length=20, choices=Channel.choices, db_index=True)
	subject = models.CharField(max_length=255, blank=True)
	body = models.TextField()
	provider_message_id = models.CharField(max_length=255, blank=True, db_index=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
	sent_at = models.DateTimeField(null=True, blank=True, db_index=True)
	response_at = models.DateTimeField(null=True, blank=True, db_index=True)
	error_message = models.TextField(blank=True)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["user", "status"], name="outreach_user_status_idx"),
			models.Index(fields=["user", "channel"], name="outreach_user_channel_idx"),
			models.Index(fields=["channel", "status"], name="outreach_channel_status_idx"),
			models.Index(fields=["sent_at", "status"], name="outreach_sent_status_idx"),
		]

	def __str__(self) -> str:
		return f"Outreach<{self.user.email}:{self.recipient_name}>"
