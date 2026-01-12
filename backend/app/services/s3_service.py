import boto3
import os
from typing import BinaryIO
from app.config import settings


class S3Service:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket = settings.AWS_S3_BUCKET

    def upload_file(self, file_obj: BinaryIO, s3_key: str) -> str:
        """Upload file to S3 and return S3 path."""
        self.client.upload_fileobj(file_obj, self.bucket, s3_key)
        return f"s3://{self.bucket}/{s3_key}"

    def upload_local_file(self, local_path: str, s3_key: str) -> str:
        """Upload local file to S3."""
        self.client.upload_file(local_path, self.bucket, s3_key)
        return f"s3://{self.bucket}/{s3_key}"

    def download_file(self, s3_key: str, local_path: str):
        """Download file from S3 to local path."""
        self.client.download_file(self.bucket, s3_key, local_path)

    def delete_file(self, s3_path: str):
        """Delete file from S3."""
        # Extract s3_key from s3://bucket/key format
        if s3_path.startswith("s3://"):
            s3_key = s3_path.split(f"{self.bucket}/", 1)[1]
        else:
            s3_key = s3_path
        self.client.delete_object(Bucket=self.bucket, Key=s3_key)

    def get_file_url(self, s3_key: str) -> str:
        """Get public URL for S3 file."""
        return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"


s3_service = S3Service()
