from django.urls import path

from .views import (
    CurrentUserView,
    DashboardView,
    GoogleLoginView,
    GoogleOAuthCallbackView,
    JobApplicationDetailView,
    JobApplicationListCreateView,
    LogoutView,
    OutreachMessageDetailView,
    OutreachMessageListCreateView,
    ResumeDetailView,
    ResumeListCreateView,
    UserPreferenceView,
)


urlpatterns = [
    path("auth/google/", GoogleLoginView.as_view(), name="google-login"),
    path("auth/google/callback/", GoogleOAuthCallbackView.as_view(), name="google-callback"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("preferences/", UserPreferenceView.as_view(), name="user-preferences"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("resumes/", ResumeListCreateView.as_view(), name="resume-list-create"),
    path("resumes/<int:pk>/", ResumeDetailView.as_view(), name="resume-detail"),
    path("applications/", JobApplicationListCreateView.as_view(), name="application-list-create"),
    path("applications/<int:pk>/", JobApplicationDetailView.as_view(), name="application-detail"),
    path("outreach/", OutreachMessageListCreateView.as_view(), name="outreach-list-create"),
    path("outreach/<int:pk>/", OutreachMessageDetailView.as_view(), name="outreach-detail"),
]