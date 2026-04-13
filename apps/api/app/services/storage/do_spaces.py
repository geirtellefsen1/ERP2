"""
DigitalOcean Spaces storage via boto3 S3 compatibility.

DO Spaces is S3-compatible so this adapter uses boto3 with a custom
endpoint_url. Signed URLs are generated via boto3's presigned_url
helper with a configurable expiry.

Credentials come from integration_configs (provider='do_spaces') at
runtime, NOT from env vars — so each agency can have their own bucket.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from .base import FileStorage, StorageError, StorageObject

logger = logging.getLogger(__name__)


# boto3 is a large import — defer it so dev environments without it
# can still import this module (e.g. to construct LocalStorage).
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    _BOTO_AVAILABLE = True
except Exception:
    _BOTO_AVAILABLE = False


class DOSpacesStorage(FileStorage):
    provider_name = "do_spaces"

    def __init__(
        self,
        endpoint: str,
        region: str,
        bucket: str,
        access_key: str,
        secret_key: str,
    ):
        if not _BOTO_AVAILABLE:
            raise StorageError(
                "boto3 is required for DOSpacesStorage. Install with: "
                "pip install boto3"
            )
        if not all([endpoint, region, bucket, access_key, secret_key]):
            raise StorageError(
                "DOSpacesStorage requires endpoint, region, bucket, "
                "access_key, and secret_key"
            )
        self.bucket = bucket
        self.endpoint = endpoint
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def put(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageObject:
        try:
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ACL="private",
            )
        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"DO Spaces put failed: {e}") from e
        return StorageObject(
            key=key,
            size_bytes=len(data),
            content_type=content_type,
            last_modified=datetime.now(timezone.utc),
        )

    def get(self, key: str) -> bytes:
        try:
            resp = self._client.get_object(Bucket=self.bucket, Key=key)
            return resp["Body"].read()
        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"DO Spaces get failed: {e}") from e

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"DO Spaces delete failed: {e}") from e

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
        except BotoCoreError as e:
            raise StorageError(f"DO Spaces head failed: {e}") from e

    def signed_url(
        self,
        key: str,
        *,
        expires_in_seconds: int = 3600,
    ) -> str:
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in_seconds,
            )
        except (BotoCoreError, ClientError) as e:
            raise StorageError(f"DO Spaces signed URL failed: {e}") from e
