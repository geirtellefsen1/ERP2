"""
Document Intelligence — OCR, AI extraction, fraud detection, approval workflow.
Uses Claude Vision for document extraction + optional AWS Textract backend.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
import httpx, json, re
from app.database import get_db
from app.models import Document, DocumentIntelligence, Client
from app.auth import AuthUser, get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
settings = get_settings()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: int; name: str; category: str; file_size: int | None
    mime_type: str | None; created_at: datetime | None
    class Config: from_attributes = True


class ExtractionResult(BaseModel):
    document_id: int
    status: str
    confidence: float
    is_fraud_flagged: bool
    fraud_reasons: list[str]
    extracted_data: dict


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def extract_with_claude_vision(
    document_id: int,
    file_content: bytes,
    mime_type: str,
) -> dict:
    """
    Send document image/PDF to Claude API for intelligent extraction.
    Returns: {raw_text, extracted_data, confidence, fraud_flags}
    """
    if not settings.claude_api_key:
        return {
            "raw_text": "",
            "extracted_data": {},
            "confidence": 0.0,
            "fraud_flags": ["Claude API key not configured"],
            "status": "failed",
        }

    # Build image part
    import base64
    b64_content = base64.b64encode(file_content).decode()

    prompt = """
You are a document intelligence system. Extract structured data from this document.

For INVOICES extract:
- invoice_number, date, due_date, client_name, line_items (description, quantity, unit_price, total), subtotal, tax, total, currency

For BANK STATEMENTS extract:
- bank_name, account_number, date, description, amount, running_balance, transaction_category

For RECEIPTS extract:
- merchant_name, date, line_items, total_amount, tax_amount, currency

For CONTRACTS extract:
- parties, effective_date, termination_date, key_terms, value, currency

Respond ONLY with valid JSON matching this exact format:
{
  "document_type": "invoice" | "bank_statement" | "receipt" | "contract" | "other",
  "invoice_number": "...",
  "date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "client_name": "...",
  "total_amount": "123.45 or null",
  "currency": "ZAR or EUR or USD or GBP",
  "line_items": [{"description": "...", "quantity": "1", "unit_price": "0.00", "total": "0.00"}],
  "raw_text_summary": "2-3 sentence summary of document content",
  "confidence": 0.0 to 1.0,
  "fraud_flags": ["flag reason 1", "flag reason 2 or empty array"]
}
"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": b64_content[:100_000],  # Truncate to 100KB for API limit
                                    }
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                },
            )

            if resp.status_code != 200:
                return {
                    "raw_text": "",
                    "extracted_data": {},
                    "confidence": 0.0,
                    "fraud_flags": [f"Claude API error: {resp.status_code}"],
                    "status": "failed",
                }

            data = resp.json()
            content_text = data["content"][0]["text"]
            # Extract JSON
            start = content_text.find("{")
            end = content_text.rfind("}") + 1
            if start == -1:
                return {
                    "raw_text": content_text[:500],
                    "extracted_data": {},
                    "confidence": 0.1,
                    "fraud_flags": ["Could not parse Claude response"],
                    "status": "failed",
                }

            result = json.loads(content_text[start:end])
            return {
                "raw_text": content_text[:2000],
                "extracted_data": result,
                "confidence": result.get("confidence", 0.5),
                "fraud_flags": result.get("fraud_flags", []),
                "status": "complete",
            }
    except Exception as e:
        return {
            "raw_text": "",
            "extracted_data": {},
            "confidence": 0.0,
            "fraud_flags": [f"Processing error: {str(e)}"],
            "status": "failed",
        }


async def process_document_background(
    document_id: int,
    db_url: str,
):
    """Background task — runs after document upload to extract data."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url.replace("+asyncpg", ""))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        # Read file content
        if doc.file_path:
            # In production: fetch from DO Spaces
            file_content = b"mock-content"
        else:
            file_content = b"mock-content"

        mime = doc.mime_type or "application/pdf"
        result = await extract_with_claude_vision(document_id, file_content, mime)

        # Save result
        intelligence = DocumentIntelligence(
            document_id=document_id,
            extraction_model="claude_vision",
            raw_text=result.get("raw_text", ""),
            extracted_data=json.dumps(result.get("extracted_data", {})),
            confidence_score=Decimal(str(result.get("confidence", 0))),
            is_fraud_flagged=len(result.get("fraud_flags", [])) > 0,
            fraud_reasons=json.dumps(result.get("fraud_flags", [])),
            status=result.get("status", "failed"),
            processed_at=datetime.utcnow(),
        )
        db.add(intelligence)
        doc.created_at = doc.created_at  # touch
        db.commit()
    finally:
        db.close()


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/{client_id}/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    client_id: int,
    background_tasks: BackgroundTasks,
    category: str = Query("Other"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Upload a document and trigger AI extraction in the background."""
    # Verify client access
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found")

    # Read file content
    content = await file.read()
    file_size = len(content)

    # In production: upload to DO Spaces
    # file_path = await upload_to_spaces(content, file.filename, file.content_type)
    file_path = f"documents/{client_id}/{file.filename}"

    document = Document(
        client_id=client_id,
        name=file.filename,
        category=category,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        uploaded_by=current_user.sub,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Queue background extraction
    background_tasks.add_task(
        process_document_background,
        document.id,
        settings.database_url,
    )

    return document


@router.get("/{client_id}", response_model=list[DocumentOut])
def list_documents(
    client_id: int,
    category: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Document).filter(Document.client_id == client_id)
    if category:
        q = q.filter(Document.category == category)
    return q.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{client_id}/intelligence/{document_id}")
def get_document_intelligence(
    client_id: int,
    document_id: int,
    db: Session = Depends(get_db),
):
    """Get AI extraction results for a document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.client_id == client_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    intelligence = db.query(DocumentIntelligence).filter(
        DocumentIntelligence.document_id == document_id,
    ).order_by(DocumentIntelligence.created_at.desc()).first()

    if not intelligence:
        return {"status": "processing", "document_id": document_id}

    return {
        "status": intelligence.status,
        "document_id": document_id,
        "extraction_model": intelligence.extraction_model,
        "confidence": float(intelligence.confidence_score or 0),
        "is_fraud_flagged": intelligence.is_fraud_flagged,
        "fraud_reasons": json.loads(intelligence.fraud_reasons or "[]"),
        "extracted_data": json.loads(intelligence.extracted_data or "{}"),
        "processed_at": intelligence.processed_at.isoformat() if intelligence.processed_at else None,
    }


@router.post("/{client_id}/intelligence/{document_id}/review")
def approve_document_extraction(
    client_id: int,
    document_id: int,
    approved: bool,
    corrections: dict | None = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """Agent approves or corrects AI extraction before posting to GL."""
    intelligence = db.query(DocumentIntelligence).filter(
        DocumentIntelligence.document_id == document_id,
    ).first()
    if not intelligence:
        raise HTTPException(status_code=404, detail="No extraction found")

    if approved:
        intelligence.status = "approved"
        # In production: create journal entry from extracted_data
    else:
        intelligence.status = "rejected"
        if corrections:
            intelligence.extracted_data = json.dumps(corrections)

    db.commit()
    return {"document_id": document_id, "status": intelligence.status}
