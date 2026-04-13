"""
File storage tests — LocalStorage, DOSpacesStorage, and the factory.

LocalStorage is exercised end-to-end against a temp directory.
DOSpacesStorage is exercised with a mocked boto3 client so the tests
don't need real DO Spaces credentials or network access.
The factory is exercised against real integration_configs rows.
"""
from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.models import Agency
from app.services import integrations as svc
from app.services.storage import (
    DOSpacesStorage,
    FileStorage,
    LocalStorage,
    StorageError,
    StorageObject,
    get_storage,
)


# ─── Shared fixtures ────────────────────────────────────────────────────


@pytest.fixture
def tmp_storage_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def local_storage(tmp_storage_dir) -> LocalStorage:
    return LocalStorage(base_dir=tmp_storage_dir)


@pytest.fixture
def sample_storage_agency(db):
    agency = Agency(name="Storage Test Agency", slug="storage-test-agency")
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


# ─── StorageObject / base contract ──────────────────────────────────────


def test_storage_object_exposes_metadata():
    obj = StorageObject(
        key="foo/bar.pdf",
        size_bytes=1234,
        content_type="application/pdf",
    )
    assert obj.key == "foo/bar.pdf"
    assert obj.size_bytes == 1234
    assert obj.content_type == "application/pdf"
    assert obj.last_modified is None


def test_local_and_do_spaces_both_subclass_filestorage():
    assert issubclass(LocalStorage, FileStorage)
    assert issubclass(DOSpacesStorage, FileStorage)


def test_provider_names_are_distinct():
    assert LocalStorage.provider_name == "local"
    assert DOSpacesStorage.provider_name == "do_spaces"


# ─── LocalStorage — happy path ──────────────────────────────────────────


def test_local_put_then_get_roundtrips_bytes(local_storage):
    payload = b"hello, storage"
    obj = local_storage.put("receipts/2026/04/abc.txt", payload, "text/plain")
    assert obj.key == "receipts/2026/04/abc.txt"
    assert obj.size_bytes == len(payload)
    assert obj.content_type == "text/plain"
    assert local_storage.get("receipts/2026/04/abc.txt") == payload


def test_local_put_creates_nested_directories(local_storage, tmp_storage_dir):
    local_storage.put("agency-1/invoices/2026/04/file.pdf", b"pdf-data")
    expected = os.path.join(
        tmp_storage_dir, "agency-1", "invoices", "2026", "04", "file.pdf"
    )
    assert os.path.exists(expected)


def test_local_exists_true_after_put(local_storage):
    local_storage.put("a/b.txt", b"x")
    assert local_storage.exists("a/b.txt") is True


def test_local_exists_false_for_missing_key(local_storage):
    assert local_storage.exists("nope/missing.txt") is False


def test_local_delete_removes_file(local_storage):
    local_storage.put("a/b.txt", b"x")
    local_storage.delete("a/b.txt")
    assert local_storage.exists("a/b.txt") is False


def test_local_delete_missing_key_is_noop(local_storage):
    # Should not raise on a key that never existed.
    local_storage.delete("never/existed.txt")


def test_local_get_missing_key_raises(local_storage):
    with pytest.raises(StorageError) as exc:
        local_storage.get("never/existed.txt")
    assert "not found" in str(exc.value).lower()


def test_local_signed_url_for_existing_file_is_file_url(local_storage):
    local_storage.put("a/b.txt", b"x")
    url = local_storage.signed_url("a/b.txt")
    assert url.startswith("file://")
    assert url.endswith("a/b.txt")


def test_local_signed_url_missing_key_raises(local_storage):
    with pytest.raises(StorageError):
        local_storage.signed_url("never/existed.txt")


# ─── LocalStorage — path traversal defense ─────────────────────────────


@pytest.mark.parametrize(
    "bad_key",
    [
        "",
        "/etc/passwd",
        "../../etc/passwd",
        "foo/../../etc/passwd",
        "foo/../../../bar",
    ],
)
def test_local_rejects_unsafe_keys(local_storage, bad_key):
    with pytest.raises(StorageError):
        local_storage.put(bad_key, b"data")


def test_local_rejects_traversal_on_read(local_storage):
    with pytest.raises(StorageError):
        local_storage.get("../../etc/passwd")


# ─── DOSpacesStorage — constructor validation ──────────────────────────


def test_do_spaces_requires_all_credentials():
    with pytest.raises(StorageError):
        DOSpacesStorage(
            endpoint="https://cap-1.digitaloceanspaces.com",
            region="cap-1",
            bucket="",           # missing
            access_key="key",
            secret_key="secret",
        )


# ─── DOSpacesStorage — mocked boto3 client ─────────────────────────────


def _make_do_spaces_with_mock_client():
    """
    Build a DOSpacesStorage whose internal boto3 client is a MagicMock,
    so the tests never hit the network.
    """
    with patch("app.services.storage.do_spaces.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        storage = DOSpacesStorage(
            endpoint="https://cap-1.digitaloceanspaces.com",
            region="cap-1",
            bucket="test-bucket",
            access_key="AKIA_TEST",
            secret_key="SECRET_TEST",
        )
    return storage, mock_client


def test_do_spaces_put_calls_client_with_private_acl():
    storage, client = _make_do_spaces_with_mock_client()
    obj = storage.put("a/b.pdf", b"pdf-bytes", "application/pdf")
    client.put_object.assert_called_once()
    kwargs = client.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "test-bucket"
    assert kwargs["Key"] == "a/b.pdf"
    assert kwargs["Body"] == b"pdf-bytes"
    assert kwargs["ContentType"] == "application/pdf"
    assert kwargs["ACL"] == "private"
    assert obj.size_bytes == len(b"pdf-bytes")
    assert obj.content_type == "application/pdf"


def test_do_spaces_get_reads_body_stream():
    storage, client = _make_do_spaces_with_mock_client()
    body = MagicMock()
    body.read.return_value = b"payload"
    client.get_object.return_value = {"Body": body}
    assert storage.get("a/b.pdf") == b"payload"
    client.get_object.assert_called_once_with(Bucket="test-bucket", Key="a/b.pdf")


def test_do_spaces_delete_forwards_to_client():
    storage, client = _make_do_spaces_with_mock_client()
    storage.delete("a/b.pdf")
    client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="a/b.pdf")


def test_do_spaces_exists_true_when_head_object_succeeds():
    storage, client = _make_do_spaces_with_mock_client()
    client.head_object.return_value = {}
    assert storage.exists("a/b.pdf") is True


def test_do_spaces_exists_false_on_client_error():
    from botocore.exceptions import ClientError
    storage, client = _make_do_spaces_with_mock_client()
    client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not found"}}, "HeadObject"
    )
    assert storage.exists("a/b.pdf") is False


def test_do_spaces_signed_url_forwards_expiry():
    storage, client = _make_do_spaces_with_mock_client()
    client.generate_presigned_url.return_value = "https://signed.example/abc"
    url = storage.signed_url("a/b.pdf", expires_in_seconds=900)
    assert url == "https://signed.example/abc"
    client.generate_presigned_url.assert_called_once()
    args, kwargs = client.generate_presigned_url.call_args
    assert args[0] == "get_object"
    assert kwargs["Params"] == {"Bucket": "test-bucket", "Key": "a/b.pdf"}
    assert kwargs["ExpiresIn"] == 900


def test_do_spaces_wraps_boto_errors_in_storage_error():
    from botocore.exceptions import ClientError
    storage, client = _make_do_spaces_with_mock_client()
    client.put_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "PutObject"
    )
    with pytest.raises(StorageError):
        storage.put("a/b.pdf", b"x")


# ─── Factory ───────────────────────────────────────────────────────────


def test_factory_force_local_returns_local(db, sample_storage_agency):
    storage = get_storage(db, sample_storage_agency.id, force_local=True)
    assert isinstance(storage, LocalStorage)


def test_factory_falls_back_to_local_without_config(db, sample_storage_agency):
    storage = get_storage(db, sample_storage_agency.id)
    assert isinstance(storage, LocalStorage)


def test_factory_falls_back_to_local_on_partial_config(db, sample_storage_agency):
    # Only endpoint set — the factory should treat this as "not configured"
    # and fall back to LocalStorage instead of crashing.
    svc.set_config(
        db,
        sample_storage_agency.id,
        "do_spaces",
        {"endpoint": "https://cap-1.digitaloceanspaces.com"},
    )
    storage = get_storage(db, sample_storage_agency.id)
    assert isinstance(storage, LocalStorage)


def test_factory_returns_do_spaces_when_fully_configured(db, sample_storage_agency):
    svc.set_config(
        db,
        sample_storage_agency.id,
        "do_spaces",
        {
            "endpoint": "https://cap-1.digitaloceanspaces.com",
            "region": "cap-1",
            "bucket": "claud-erp-files",
            "access_key": "AKIA_FULL",
            "secret_key": "SECRET_FULL",
        },
    )
    with patch("app.services.storage.do_spaces.boto3") as mock_boto3:
        mock_boto3.client.return_value = MagicMock()
        storage = get_storage(db, sample_storage_agency.id)
    assert isinstance(storage, DOSpacesStorage)
    assert storage.bucket == "claud-erp-files"
