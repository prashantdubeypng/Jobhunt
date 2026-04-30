from __future__ import annotations

from django.db.models import Count

from ..models import JobApplication, OutreachMessage, Resume


class DashboardService:
    def build_summary(self, user) -> dict:
        applications = JobApplication.objects.filter(user=user)
        resumes = Resume.objects.filter(user=user)
        outreach = OutreachMessage.objects.filter(user=user)

        application_counts = {
            item["status"]: item["count"]
            for item in applications.values("status").annotate(count=Count("id"))
        }

        return {
            "application_counts": application_counts,
            "resume_count": resumes.count(),
            "outreach_count": outreach.count(),
            "email_count": outreach.filter(channel="email").count(),
            "linkedin_count": outreach.filter(channel="linkedin").count(),
            "recent_applications": applications.select_related("resume")[:5],
            "recent_resumes": resumes[:5],
            "recent_outreach": outreach.select_related("application", "resume")[:5],
        }