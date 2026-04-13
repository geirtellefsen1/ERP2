"""Factory that picks the right FileStorage based on agency config."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.services import integrations as svc
from app.services.storage.base import FileStorage, StorageError
from app.services.storage.do_spaces import DOSpacesStorage
from app.services.storage.local import LocalStorage


def get_storage(
    db: Session,
    agency_id: int,
    *,
    force_local: bool = False,
) -> FileStorage:
    """
    Return a FileStorage for the given agency.

    If `force_local=True` or the agency has no DO Spaces config,
    returns LocalStorage so dev/test flows work out of the box.
    """
    if force_local:
        return LocalStorage()

    config = svc.get_config(db, agency_id, "do_spaces")
    required = ["endpoint", "region", "bucket", "access_key", "secret_key"]
    if not all(config.get(k) for k in required):
        return LocalStorage()

    try:
        return DOSpacesStorage(
            endpoint=config["endpoint"],
            region=config["region"],
            bucket=config["bucket"],
            access_key=config["access_key"],
            secret_key=config["secret_key"],
        )
    except StorageError:
        return LocalStorage()
