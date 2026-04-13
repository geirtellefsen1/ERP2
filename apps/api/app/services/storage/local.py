"""
Local filesystem storage for dev and tests.

Files live under a base directory (default /tmp/claud-erp-storage).
"Signed URLs" are file:// URLs — obviously not safe for production,
but perfect for local dev where there's no S3 or Spaces to talk to.
"""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .base import FileStorage, StorageError, StorageObject


class LocalStorage(FileStorage):
    provider_name = "local"

    def __init__(self, base_dir: str = "/tmp/claud-erp-storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """
        Join base_dir + key safely. Rejects any key that would escape
        the base directory (path traversal defense).
        """
        if not key or key.startswith("/") or ".." in key.split("/"):
            raise StorageError(f"Invalid storage key: {key!r}")
        path = (self.base_dir / key).resolve()
        # Defense in depth — the resolved path must still live under base_dir
        if not str(path).startswith(str(self.base_dir.resolve())):
            raise StorageError(f"Key escapes base directory: {key!r}")
        return path

    def put(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageObject:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return StorageObject(
            key=key,
            size_bytes=len(data),
            content_type=content_type,
            last_modified=datetime.now(timezone.utc),
        )

    def get(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise StorageError(f"Object not found: {key}")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def signed_url(
        self,
        key: str,
        *,
        expires_in_seconds: int = 3600,
    ) -> str:
        path = self._resolve(key)
        if not path.exists():
            raise StorageError(f"Object not found: {key}")
        # file:// URL is fine for dev; production uses DOSpacesStorage
        return f"file://{path}"
