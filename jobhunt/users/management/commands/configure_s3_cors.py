"""
Django management command to configure S3 CORS policy
Usage: python manage.py configure_s3_cors
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from jobhunt.users.Services.s3_cors_config import S3CORSConfigurator


class Command(BaseCommand):
    help = "Configure CORS policy on S3 bucket for presigned direct uploads"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--verify",
            action="store_true",
            help="Only verify current CORS configuration without making changes",
        )
    
    def handle(self, *args, **options):
        # Validate required settings
        required_settings = [
            "AWS_S3_BUCKET_NAME",
            "AWS_S3_REGION_NAME",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]
        
        missing = [s for s in required_settings if not getattr(settings, s, None)]
        if missing:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Missing required AWS settings: {', '.join(missing)}\n"
                    "Please set these in .env file"
                )
            )
            return
        
        try:
            configurator = S3CORSConfigurator()
            
            self.stdout.write(self.style.SUCCESS("🔧 S3 CORS Configuration Tool"))
            self.stdout.write(f"   Bucket: {settings.AWS_S3_BUCKET_NAME}")
            self.stdout.write(f"   Region: {settings.AWS_S3_REGION_NAME}\n")
            
            if options["verify"]:
                self.stdout.write("📋 Checking current CORS configuration...\n")
                if configurator.verify_cors():
                    self.stdout.write(
                        self.style.SUCCESS("✅ CORS is properly configured")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠️  CORS is not configured or incomplete")
                    )
            else:
                self.stdout.write("📝 Applying CORS policy...\n")
                configurator.apply_cors_policy()
                
                self.stdout.write(self.style.SUCCESS("\n✅ CORS configuration complete!\n"))
                self.stdout.write("   Allowed origins:")
                for origin in S3CORSConfigurator.get_cors_policy()["CORSRules"][0]["AllowedOrigins"]:
                    self.stdout.write(f"   • {origin}")
                self.stdout.write("\n   Allowed methods: GET, PUT, POST, DELETE, HEAD")
                self.stdout.write("   Exposed headers: ETag, x-amz-version-id\n")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
