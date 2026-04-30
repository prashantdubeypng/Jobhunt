import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from jobhunt.users.models import GoogleIdentity, JobApplication, OutreachMessage, Resume, UserPreference


User = get_user_model()


@pytest.fixture
def user(db):
	return User.objects.create_user(
		username="tester",
		email="tester@example.com",
		password="strongpassword123",
	)


@pytest.fixture
def authenticated_client(api_client, user):
	api_client.force_authenticate(user=user)
	return api_client


@pytest.fixture
def related_objects(user):
	preference = UserPreference.objects.create(
		user=user,
		target_job_titles=["Backend Engineer"],
		auto_apply=True,
	)
	resume = Resume.objects.create(
		user=user,
		title="Primary Resume",
		parsed_text="Python, Django",
		is_primary=True,
	)
	application = JobApplication.objects.create(
		user=user,
		resume=resume,
		company_name="Acme Inc",
		role_title="Software Engineer",
		status=JobApplication.Status.APPLIED,
		source=JobApplication.Source.LINKEDIN,
	)
	outreach = OutreachMessage.objects.create(
		user=user,
		application=application,
		resume=resume,
		recipient_name="Founder",
		recipient_email="founder@acme.com",
		channel=OutreachMessage.Channel.EMAIL,
		subject="Interested in your role",
		body="Hello, I am interested in the role.",
		status=OutreachMessage.Status.SENT,
	)
	return {
		"preference": preference,
		"resume": resume,
		"application": application,
		"outreach": outreach,
	}


def test_google_login_redirects_to_google(api_client, monkeypatch):
	class FakeGoogleService:
		def get_login_url(self, state=None, include_gmail_scope=True):
			return f"https://accounts.google.com/mock?state={state}&gmail={include_gmail_scope}"

	class FakeAuthService:
		def __init__(self):
			self.google_service = FakeGoogleService()

	monkeypatch.setattr("jobhunt.users.views.GoogleAuthenticationService", FakeAuthService)

	response = api_client.get(reverse("google-login") + "?state=abc&include_gmail_scope=false")

	assert response.status_code == 302
	assert response["Location"] == "https://accounts.google.com/mock?state=abc&gmail=False"


def test_google_callback_requires_code(api_client):
	response = api_client.get(reverse("google-callback"))

	assert response.status_code == 400
	assert response.data["detail"] == "Missing Google authorization code."


def test_google_callback_redirects_with_token(api_client, monkeypatch, user):
	class FakeResult:
		def __init__(self):
			self.app_token = "signed-token"
			self.user = user
			self.created = True

	class FakeAuthService:
		def login_or_create_user(self, code):
			assert code == "oauth-code"
			return FakeResult()

	monkeypatch.setattr("jobhunt.users.views.GoogleAuthenticationService", lambda: FakeAuthService())

	response = api_client.get(reverse("google-callback") + "?code=oauth-code")

	assert response.status_code == 302
	assert response["Location"].startswith("http://localhost:5173/auth/google/callback#")
	assert "token=signed-token" in response["Location"]
	assert f"user_id={user.id}" in response["Location"]
	assert "email=tester%40example.com" in response["Location"]
	assert "created=true" in response["Location"]


def test_logout_returns_redirect_url(authenticated_client, monkeypatch, user):
	GoogleIdentity.objects.create(user=user, access_token="google-access-token")

	called = {}

	class FakeGoogleService:
		def revoke_token(self, token):
			called["token"] = token

	class FakeAuthService:
		def __init__(self):
			self.google_service = FakeGoogleService()

	monkeypatch.setattr("jobhunt.users.views.GoogleAuthenticationService", FakeAuthService)

	response = authenticated_client.post(reverse("logout"))

	assert response.status_code == 200
	assert response.data["detail"] == "Logged out successfully."
	assert response.data["redirect_url"] == "http://localhost:5173"
	assert called["token"] == "google-access-token"


def test_current_user_returns_profile(authenticated_client, related_objects, user):
	response = authenticated_client.get(reverse("current-user"))

	assert response.status_code == 200
	assert response.data["email"] == user.email
	assert response.data["google_identity"] is None
	assert response.data["preference"]["auto_apply"] is True


def test_preferences_get_creates_default(authenticated_client):
	response = authenticated_client.get(reverse("user-preferences"))

	assert response.status_code == 200
	assert response.data["weekly_digest"] is True


def test_preferences_patch_updates_values(authenticated_client, related_objects):
	response = authenticated_client.patch(
		reverse("user-preferences"),
		{"auto_email": True, "linkedin_outreach": True},
		format="json",
	)

	assert response.status_code == 200
	assert response.data["auto_email"] is True
	assert response.data["linkedin_outreach"] is True


def test_dashboard_returns_summary(authenticated_client, monkeypatch, related_objects):
	resume = related_objects["resume"]
	application = related_objects["application"]
	outreach = related_objects["outreach"]

	class FakeDashboardService:
		def build_summary(self, user):
			return {
				"application_counts": {"applied": 1},
				"resume_count": 1,
				"outreach_count": 1,
				"email_count": 1,
				"linkedin_count": 0,
				"recent_applications": JobApplication.objects.filter(pk=application.pk),
				"recent_resumes": Resume.objects.filter(pk=resume.pk),
				"recent_outreach": OutreachMessage.objects.filter(pk=outreach.pk),
			}

	monkeypatch.setattr("jobhunt.users.views.DashboardService", FakeDashboardService)

	response = authenticated_client.get(reverse("dashboard"))

	assert response.status_code == 200
	assert response.data["stats"]["resume_count"] == 1
	assert response.data["recent_applications"][0]["company_name"] == "Acme Inc"
	assert response.data["recent_resumes"][0]["title"] == "Primary Resume"
	assert response.data["recent_outreach"][0]["recipient_name"] == "Founder"


def test_resume_list_and_create(authenticated_client, related_objects):
	response = authenticated_client.get(reverse("resume-list-create"))
	assert response.status_code == 200
	assert len(response.data) == 1

	response = authenticated_client.post(
		reverse("resume-list-create"),
		{"title": "Secondary Resume", "parsed_text": "Go, Django", "is_primary": False},
		format="json",
	)

	assert response.status_code == 201
	assert response.data["title"] == "Secondary Resume"


def test_resume_detail_update_and_delete(authenticated_client, related_objects):
	resume = related_objects["resume"]
	url = reverse("resume-detail", kwargs={"pk": resume.pk})

	response = authenticated_client.patch(url, {"title": "Updated Resume"}, format="json")
	assert response.status_code == 200
	assert response.data["title"] == "Updated Resume"

	response = authenticated_client.delete(url)
	assert response.status_code == 204


def test_application_list_and_create(authenticated_client, related_objects):
	resume = related_objects["resume"]

	response = authenticated_client.get(reverse("application-list-create"))
	assert response.status_code == 200
	assert len(response.data) == 1

	response = authenticated_client.post(
		reverse("application-list-create"),
		{
			"resume": resume.pk,
			"company_name": "NewCo",
			"role_title": "Platform Engineer",
			"status": JobApplication.Status.DRAFT,
			"source": JobApplication.Source.MANUAL,
		},
		format="json",
	)

	assert response.status_code == 201
	assert response.data["company_name"] == "NewCo"


def test_application_detail_updates_status_history(authenticated_client, related_objects):
	application = related_objects["application"]
	url = reverse("application-detail", kwargs={"pk": application.pk})

	response = authenticated_client.patch(url, {"status": JobApplication.Status.INTERVIEW}, format="json")

	assert response.status_code == 200
	assert response.data["status"] == JobApplication.Status.INTERVIEW
	assert len(response.data["status_history"]) == 1
	assert response.data["status_history"][0]["previous_status"] == JobApplication.Status.APPLIED


def test_outreach_list_and_create(authenticated_client, related_objects):
	application = related_objects["application"]
	resume = related_objects["resume"]

	response = authenticated_client.get(reverse("outreach-list-create"))
	assert response.status_code == 200
	assert len(response.data) == 1

	response = authenticated_client.post(
		reverse("outreach-list-create"),
		{
			"application": application.pk,
			"resume": resume.pk,
			"recipient_name": "Another Founder",
			"recipient_email": "hello@example.com",
			"channel": OutreachMessage.Channel.LINKEDIN,
			"subject": "Hello",
			"body": "Message body",
			"status": OutreachMessage.Status.QUEUED,
		},
		format="json",
	)

	assert response.status_code == 201
	assert response.data["recipient_name"] == "Another Founder"


def test_outreach_detail_update_and_delete(authenticated_client, related_objects):
	outreach = related_objects["outreach"]
	url = reverse("outreach-detail", kwargs={"pk": outreach.pk})

	response = authenticated_client.patch(url, {"status": OutreachMessage.Status.REPLIED}, format="json")
	assert response.status_code == 200
	assert response.data["status"] == OutreachMessage.Status.REPLIED

	response = authenticated_client.delete(url)
	assert response.status_code == 204
