"""
File storage abstraction.

Three implementations:
  - LocalStorage: filesystem, used for dev and tests
  - DOSpacesStorage: S3-compatible DO Spaces
  - (S3Storage: AWS S3 can slot in here later)

All three expose the same interface so router code doesn't care
which one's actually writing bytes. Signed URLs are produced so
clients can download private objects without the API streaming them
through itself.
"""
from .base import (
    FileStorage,
    StorageError,
    StorageObject,
)
from .local import LocalStorage
from .do_spaces import DOSpacesStorage
from .factory import get_storage

__all__ = [
    "FileStorage",
    "StorageError",
    "StorageObject",
    "LocalStorage",
    "DOSpacesStorage",
    "get_storage",
]
