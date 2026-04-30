import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from jobhunt.users.Services.s3_service import PresignedUploadData, S3PresignedUploadService
from jobhunt.users.models import Resume


User = get_user_model()


@pytest.fixture
def user(db):
	return User.objects.create_user(
		username="resume-uploader",
		email="resume@example.com",
		password="strongpassword123",
	)


@pytest.fixture
def authenticated_client(api_client, user):
	api_client.force_authenticate(user=user)
	return api_client


def test_s3_service_builds_key_and_url(monkeypatch):
	class FakeS3Client:
		def generate_presigned_url(self, ClientMethod, Params, ExpiresIn, HttpMethod):
			assert ClientMethod == "put_object"
			assert Params["Bucket"] == "bucket-name"
			assert Params["ContentType"] == "application/pdf"
			assert HttpMethod == "PUT"
			return "https://signed-upload-url"

	monkeypatch.setattr("jobhunt.users.Services.s3_service.boto3.client", lambda *args, **kwargs: FakeS3Client())

	service = S3PresignedUploadService(bucket_name="bucket-name", region_name="us-east-1")
	result = service.create_presigned_upload(
		user_id=7,
		resume_id=11,
		filename="resume.pdf",
		content_type="application/pdf",
	)

	assert isinstance(result, PresignedUploadData)
	assert result.presigned_url == "https://signed-upload-url"
	assert result.s3_key.startswith("resumes/7/11/")
	assert result.s3_key.endswith("resume.pdf")
	assert result.s3_url == "https://bucket-name.s3.amazonaws.com/" + result.s3_key


def test_resume_upload_initiate_creates_resume_and_returns_presigned_url(authenticated_client, monkeypatch):
	class FakeUploadData:
		def __init__(self):
			self.s3_key = "resumes/1/1/key_resume.pdf"
			self.s3_url = "https://bucket-name.s3.amazonaws.com/resumes/1/1/key_resume.pdf"
			self.presigned_url = "https://signed-upload-url"
			self.expires_in = 900

	class FakeService:
		def create_presigned_upload(self, **kwargs):
			return FakeUploadData()

	monkeypatch.setattr("jobhunt.users.views.S3PresignedUploadService", FakeService)

	response = authenticated_client.post(
		reverse("resume-upload-initiate"),
		{
			"title": "Primary Resume",
			"filename": "resume.pdf",
			"content_type": "application/pdf",
			"file_size": 12345,
			"parsed_text": "Python, Django",
			"notes": "Main resume",
			"is_primary": True,
		},
		format="json",
	)

	assert response.status_code == 201
	assert response.data["presigned_url"] == "https://signed-upload-url"
	assert response.data["resume"]["title"] == "Primary Resume"
	assert response.data["resume"]["upload_status"] == Resume.UploadStatus.UPLOADING
	assert response.data["resume"]["s3_url"] == "https://bucket-name.s3.amazonaws.com/resumes/1/1/key_resume.pdf"
	assert Resume.objects.count() == 1


def test_resume_upload_complete_marks_uploaded(authenticated_client, monkeypatch):
	class FakeUploadData:
		def __init__(self):
			self.s3_key = "resumes/1/1/key_resume.pdf"
			self.s3_url = "https://bucket-name.s3.amazonaws.com/resumes/1/1/key_resume.pdf"
			self.presigned_url = "https://signed-upload-url"
			self.expires_in = 900

	class FakeService:
		def create_presigned_upload(self, **kwargs):
			return FakeUploadData()

	monkeypatch.setattr("jobhunt.users.views.S3PresignedUploadService", FakeService)

	init_response = authenticated_client.post(
		reverse("resume-upload-initiate"),
		{
			"title": "Primary Resume",
			"filename": "resume.pdf",
		},
		format="json",
	)

	resume_id = init_response.data["resume"]["id"]
	complete_response = authenticated_client.post(
		reverse("resume-upload-complete", kwargs={"pk": resume_id}),
		{
			"s3_key": "resumes/1/1/key_resume.pdf",
			"s3_url": "https://bucket-name.s3.amazonaws.com/resumes/1/1/key_resume.pdf",
		},
		format="json",
	)

	assert complete_response.status_code == 200
	assert complete_response.data["upload_status"] == Resume.UploadStatus.COMPLETED
	assert complete_response.data["s3_key"] == "resumes/1/1/key_resume.pdf"
