import os
from dotenv import load_dotenv
import boto3

# LOAD ENV — PHẢI Ở ĐẦU FILE
load_dotenv(dotenv_path=r"D:\Dự án TT\notebooklm\backend\.env")

AWS_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION")

print("DEBUG BUCKET =", AWS_BUCKET)
print("DEBUG REGION =", AWS_REGION)

if not AWS_BUCKET:
    raise RuntimeError("AWS_S3_BUCKET is None. Check .env file")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
)

def upload_local_file(local_path: str, s3_path: str) -> str:
    s3_client.upload_file(
        Filename=local_path,
        Bucket=AWS_BUCKET,
        Key=s3_path,
    )
    return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_path}"


if __name__ == "__main__":
    local_path = r"C:\Users\Admin\Downloads\test.pdf"
    s3_path = "test/test.pdf"

    url = upload_local_file(local_path, s3_path)
    print("UPLOAD SUCCESS:", url)
