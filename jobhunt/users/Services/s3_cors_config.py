"""
S3 CORS Configuration helper
Configures CORS on S3 bucket to allow direct PUT uploads from the frontend
"""
import boto3
from django.conf import settings
from botocore.exceptions import ClientError


class S3CORSConfigurator:
    """Configure CORS policy on S3 bucket for presigned uploads"""
    
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
    
    @staticmethod
    def get_cors_policy(allowed_origins=None):
        """
        Generate CORS policy for S3 bucket
        
        Args:
            allowed_origins: List of origins to allow (default: localhost dev + production)
        
        Returns:
            dict: CORS policy configuration
        """
        if allowed_origins is None:
            allowed_origins = [
                "http://localhost:5173",  # Local Vite dev server
                "http://localhost:3000",  # Alternative local dev port
                "http://localhost:8000",  # Django dev server
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
            ]
            # Add production origins if FRONTEND_URL is set
            if hasattr(settings, "FRONTEND_URL") and settings.FRONTEND_URL:
                allowed_origins.append(settings.FRONTEND_URL)
        
        return {
            "CORSRules": [
                {
                    "AllowedOrigins": allowed_origins,
                    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
                    "AllowedHeaders": ["*"],
                    "ExposeHeaders": ["ETag", "x-amz-version-id"],
                    "MaxAgeSeconds": 3000,
                }
            ]
        }
    
    def apply_cors_policy(self, allowed_origins=None):
        """
        Apply CORS policy to the S3 bucket
        
        Args:
            allowed_origins: List of origins to allow
        
        Returns:
            bool: True if successful, False otherwise
        
        Raises:
            ClientError: If S3 operation fails
        """
        try:
            cors_policy = self.get_cors_policy(allowed_origins)
            self.client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration=cors_policy
            )
            print(f"✓ CORS policy applied to bucket: {self.bucket_name}")
            print(f"✓ Region: {settings.AWS_S3_REGION_NAME}")
            print(f"✓ Allowed origins: {cors_policy['CORSRules'][0]['AllowedOrigins']}")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            print(f"✗ Failed to apply CORS policy: {error_code}")
            print(f"  Details: {e.response['Error']['Message']}")
            raise
    
    def get_cors_policy_current(self):
        """
        Get the current CORS policy from the S3 bucket
        
        Returns:
            dict: Current CORS configuration
        """
        try:
            response = self.client.get_bucket_cors(Bucket=self.bucket_name)
            return response["CORSConfiguration"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
                print(f"✗ No CORS policy configured on bucket: {self.bucket_name}")
                return None
            raise
    
    def verify_cors(self):
        """
        Verify CORS is properly configured
        
        Returns:
            bool: True if CORS is configured correctly
        """
        try:
            cors_config = self.get_cors_policy_current()
            if not cors_config:
                return False
            
            rules = cors_config.get("CORSRules", [])
            if not rules:
                return False
            
            rule = rules[0]
            has_put = "PUT" in rule.get("AllowedMethods", [])
            has_origins = len(rule.get("AllowedOrigins", [])) > 0
            
            print(f"✓ CORS configured: {has_put and has_origins}")
            return has_put and has_origins
        except ClientError as e:
            print(f"✗ Failed to verify CORS: {e}")
            return False
