from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .Services.auth_service import GoogleAuthenticationService
from .Services.dashboard_service import DashboardService
from .Services.s3_service import S3PresignedUploadService
from .authentication import AppTokenAuthentication
from .models import JobApplication, OutreachMessage, Resume, UserPreference
from .serializers import (
	JobApplicationSerializer,
	OutreachMessageSerializer,
	ResumeSerializer,
	ResumeUploadInitiateSerializer,
	UserPreferenceSerializer,
	UserSerializer,
)


class PublicAPIView(APIView):
	permission_classes = [AllowAny]


class ProtectedAPIView(APIView):
	authentication_classes = [AppTokenAuthentication, SessionAuthentication]
	permission_classes = [IsAuthenticated]


class ProtectedListCreateAPIView(generics.ListCreateAPIView):
	authentication_classes = [AppTokenAuthentication, SessionAuthentication]
	permission_classes = [IsAuthenticated]


class ProtectedRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
	authentication_classes = [AppTokenAuthentication, SessionAuthentication]
	permission_classes = [IsAuthenticated]


class GoogleLoginView(PublicAPIView):
	def get(self, request, *args, **kwargs):
		include_gmail_scope = request.query_params.get("include_gmail_scope", "true").lower() != "false"
		state = request.query_params.get("state")
		login_url = GoogleAuthenticationService().google_service.get_login_url(
			state=state,
			include_gmail_scope=include_gmail_scope,
		)
		return redirect(login_url)


class GoogleOAuthCallbackView(PublicAPIView):
	def get(self, request, *args, **kwargs):
		code = request.query_params.get("code")
		if not code:
			return Response({"detail": "Missing Google authorization code."}, status=status.HTTP_400_BAD_REQUEST)

		try:
			result = GoogleAuthenticationService().login_or_create_user(code)
		except Exception as exc:  # noqa: BLE001 - intentionally mapped to API error
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
		fragment = urlencode(
			{
				"token": result.app_token,
				"user_id": result.user.id,
				"email": result.user.email,
				"created": str(result.created).lower(),
			}
		)
		return redirect(f"{frontend_url}/auth/google/callback#{fragment}")


class LogoutView(ProtectedAPIView):
	def post(self, request, *args, **kwargs):
		google_identity = getattr(request.user, "google_identity", None)
		if google_identity and google_identity.access_token:
			try:
				GoogleAuthenticationService().google_service.revoke_token(google_identity.access_token)
			except Exception:
				pass

		logout(request)
		frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
		return Response(
			{
				"detail": "Logged out successfully.",
				"redirect_url": frontend_url,
			},
			status=status.HTTP_200_OK,
		)


class CurrentUserView(ProtectedAPIView):
	def get(self, request, *args, **kwargs):
		serializer = UserSerializer(request.user)
		return Response(serializer.data)


class UserPreferenceView(ProtectedAPIView):
	def get(self, request, *args, **kwargs):
		preference, _ = UserPreference.objects.get_or_create(user=request.user)
		return Response(UserPreferenceSerializer(preference).data)

	def patch(self, request, *args, **kwargs):
		preference, _ = UserPreference.objects.get_or_create(user=request.user)
		serializer = UserPreferenceSerializer(preference, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data)


class DashboardView(ProtectedAPIView):
	def get(self, request, *args, **kwargs):
		summary = DashboardService().build_summary(request.user)
		return Response(
			{
				"stats": {
					"application_counts": summary["application_counts"],
					"resume_count": summary["resume_count"],
					"outreach_count": summary["outreach_count"],
					"email_count": summary["email_count"],
					"linkedin_count": summary["linkedin_count"],
				},
				"recent_applications": JobApplicationSerializer(summary["recent_applications"], many=True).data,
				"recent_resumes": ResumeSerializer(summary["recent_resumes"], many=True).data,
				"recent_outreach": OutreachMessageSerializer(summary["recent_outreach"], many=True).data,
			}
		)


class ResumeListCreateView(ProtectedListCreateAPIView):
	serializer_class = ResumeSerializer

	def get_queryset(self):
		return Resume.objects.filter(user=self.request.user)

	def perform_create(self, serializer):
		is_primary = serializer.validated_data.get("is_primary", False)
		if is_primary:
			Resume.objects.filter(user=self.request.user, is_primary=True).update(is_primary=False)
		serializer.save(user=self.request.user)


class ResumeUploadInitiateView(ProtectedAPIView):
	def post(self, request, *args, **kwargs):
		serializer = ResumeUploadInitiateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		resume = Resume.objects.create(
			user=request.user,
			title=serializer.validated_data["title"],
			original_filename=serializer.validated_data["filename"],
			content_type=serializer.validated_data.get("content_type", ""),
			file_size=serializer.validated_data.get("file_size"),
			parsed_text=serializer.validated_data.get("parsed_text", ""),
			notes=serializer.validated_data.get("notes", ""),
			is_primary=serializer.validated_data.get("is_primary", False),
			upload_status=Resume.UploadStatus.UPLOADING,
		)

		if resume.is_primary:
			Resume.objects.filter(user=request.user, is_primary=True).exclude(pk=resume.pk).update(is_primary=False)

		upload_service = S3PresignedUploadService()
		upload_data = upload_service.create_presigned_upload(
			user_id=request.user.id,
			resume_id=resume.id,
			filename=resume.original_filename or serializer.validated_data["filename"],
			content_type=resume.content_type or "application/octet-stream",
		)
		resume.s3_key = upload_data.s3_key
		resume.s3_url = upload_data.s3_url
		resume.save(update_fields=["s3_key", "s3_url", "upload_status", "updated_at"])

		return Response(
			{
				"id": resume.id,
				"resume": ResumeSerializer(resume).data,
				"presigned_url": upload_data.presigned_url,
				"s3_key": upload_data.s3_key,
				"s3_url": upload_data.s3_url,
				"expires_in": upload_data.expires_in,
			},
			status=status.HTTP_201_CREATED,
		)


class ResumeUploadCompleteView(ProtectedAPIView):
	def post(self, request, pk, *args, **kwargs):
		resume = get_object_or_404(Resume, pk=pk, user=request.user)
		resume.upload_status = Resume.UploadStatus.COMPLETED
		resume.uploaded_at = timezone.now()
		if request.data.get("s3_key"):
			resume.s3_key = request.data["s3_key"]
		if request.data.get("s3_url"):
			resume.s3_url = request.data["s3_url"]
		resume.save(update_fields=["s3_key", "s3_url", "upload_status", "uploaded_at", "updated_at"])
		return Response(ResumeSerializer(resume).data, status=status.HTTP_200_OK)


class ResumeDetailView(ProtectedRetrieveUpdateDestroyAPIView):
	serializer_class = ResumeSerializer

	def get_queryset(self):
		return Resume.objects.filter(user=self.request.user)

	def perform_update(self, serializer):
		is_primary = serializer.validated_data.get("is_primary", False)
		if is_primary:
			Resume.objects.filter(user=self.request.user, is_primary=True).exclude(pk=self.get_object().pk).update(is_primary=False)
		serializer.save()

	def perform_destroy(self, instance):
		if instance.s3_key:
			try:
				S3PresignedUploadService().delete_object(instance.s3_key)
			except Exception:
				pass
		instance.delete()


class JobApplicationListCreateView(ProtectedListCreateAPIView):
	serializer_class = JobApplicationSerializer

	def get_queryset(self):
		return JobApplication.objects.filter(user=self.request.user).select_related("resume")

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class JobApplicationDetailView(ProtectedRetrieveUpdateDestroyAPIView):
	serializer_class = JobApplicationSerializer

	def get_queryset(self):
		return JobApplication.objects.filter(user=self.request.user).select_related("resume")

	def perform_update(self, serializer):
		previous_status = self.get_object().status
		application = serializer.save()
		new_status = application.status
		if previous_status != new_status:
			application.status_history.create(
				previous_status=previous_status,
				new_status=new_status,
				note="Status updated from the API.",
			)


class OutreachMessageListCreateView(ProtectedListCreateAPIView):
	serializer_class = OutreachMessageSerializer

	def get_queryset(self):
		return OutreachMessage.objects.filter(user=self.request.user).select_related("application", "resume")

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class OutreachMessageDetailView(ProtectedRetrieveUpdateDestroyAPIView):
	serializer_class = OutreachMessageSerializer

	def get_queryset(self):
		return OutreachMessage.objects.filter(user=self.request.user).select_related("application", "resume")
