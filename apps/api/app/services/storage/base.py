"""Abstract file storage interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class StorageObject:
    """Metadata for a stored file."""
    key: str                         # e.g. "agency-42/receipts/2026/04/abc123.pdf"
    size_bytes: int
    content_type: str
    last_modified: Optional[datetime] = None


class StorageError(Exception):
    """Raised on any storage operation failure."""


class FileStorage(ABC):
    """Interface every storage backend must implement."""

    provider_name: str

    @abstractmethod
    def put(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> StorageObject: ...

    @abstractmethod
    def get(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def signed_url(
        self,
        key: str,
        *,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Return a presigned URL the browser can GET without auth."""
