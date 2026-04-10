from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import documents

# Create a test app with the documents router included
# (main.py will integrate this router later; tests must be self-contained)
test_app = FastAPI()
test_app.include_router(documents.router)

client = TestClient(test_app)


def test_list_documents_requires_auth():
    response = client.get("/documents")
    assert response.status_code == 401


def test_get_document_requires_auth():
    response = client.get("/documents/1")
    assert response.status_code == 401


def test_upload_document_requires_auth():
    response = client.post(
        "/documents/upload?client_id=1",
        files={"file": ("test.pdf", b"fake-pdf-content", "application/pdf")},
    )
    assert response.status_code == 401


def test_review_queue_requires_auth():
    response = client.get("/documents/review-queue")
    assert response.status_code == 401


def test_approve_document_requires_auth():
    response = client.post("/documents/1/approve")
    assert response.status_code == 401


def test_reject_document_requires_auth():
    response = client.post("/documents/1/reject")
    assert response.status_code == 401


def test_upload_requires_file():
    response = client.post(
        "/documents/upload?client_id=1",
        headers={"Authorization": "Bearer invalid"},
    )
    # Either 401 (bad token) or 422 (missing file) is acceptable
    assert response.status_code in (401, 422)
