import os
import boto3
from botocore.config import Config


def _get_client():
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )



def upload_compressed(applicant_id: str, doc_type: str, data: bytes, fmt: str = "jpeg") -> str | None:
    """Upload compressed bytes to R2. Returns public URL or None on failure."""
    try:
        bucket = os.environ["R2_BUCKET_NAME"]
        public_url = os.environ["R2_PUBLIC_URL"].rstrip("/")
        ext = "pdf" if fmt == "pdf" else "jpg"
        content_type = "application/pdf" if fmt == "pdf" else "image/jpeg"
        key = f"compressed/{applicant_id}/{doc_type}.{ext}"

        _get_client().put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return f"{public_url}/{key}"
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"R2 upload failed for {doc_type}: {e}")
        return None
