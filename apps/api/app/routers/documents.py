from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.models import Document
from app.schemas.document import DocumentResponse, DocumentUploadResponse, DocumentListResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    client_id: int = Query(...),
    document_type: str = Query("invoice"),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Upload a document for a client. Saves metadata to the documents table."""
    ctx = await get_current_user(credentials)

    file_content = await file.read()
    file_size = len(file_content)

    # In production, upload to cloud storage; here we store a local path placeholder
    file_url = f"/uploads/{ctx.agency_id}/{client_id}/{file.filename}"

    doc = Document(
        agency_id=ctx.agency_id,
        client_id=client_id,
        document_type=document_type,
        file_name=file.filename,
        file_url=file_url,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return DocumentUploadResponse(
        id=doc.id,
        file_name=doc.file_name,
        status=doc.status,
        message="Document uploaded successfully",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    client_id: int = Query(None),
    page: int = 1,
    per_page: int = 20,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """List documents for the current agency, optionally filtered by client_id."""
    ctx = await get_current_user(credentials)
    query = db.query(Document).filter(Document.agency_id == ctx.agency_id)

    if client_id is not None:
        query = query.filter(Document.client_id == client_id)

    total = query.count()
    docs = query.order_by(Document.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return DocumentListResponse(items=docs, total=total, page=page, per_page=per_page)


@router.get("/review-queue", response_model=DocumentListResponse)
async def review_queue(
    page: int = 1,
    per_page: int = 20,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get documents with status 'pending' for the current agency."""
    ctx = await get_current_user(credentials)
    query = db.query(Document).filter(
        Document.agency_id == ctx.agency_id,
        Document.status == "pending",
    )
    total = query.count()
    docs = query.order_by(Document.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return DocumentListResponse(items=docs, total=total, page=page, per_page=per_page)


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Get a specific document by ID."""
    ctx = await get_current_user(credentials)
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.agency_id == ctx.agency_id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/{doc_id}/approve", response_model=DocumentResponse)
async def approve_document(
    doc_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Approve a document — sets status to 'posted'."""
    ctx = await get_current_user(credentials)
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.agency_id == ctx.agency_id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "posted"
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{doc_id}/reject", response_model=DocumentResponse)
async def reject_document(
    doc_id: int,
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Reject a document — sets status to 'failed'."""
    ctx = await get_current_user(credentials)
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.agency_id == ctx.agency_id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "failed"
    db.commit()
    db.refresh(doc)
    return doc
