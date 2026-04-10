from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    agency_id: int
    client_id: int
    document_type: str
    file_name: str
    file_url: str
    file_size: int
    mime_type: str
    status: str
    extraction_confidence: Optional[int] = None
    extracted_data: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    id: int
    file_name: str
    status: str
    message: str


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    per_page: int
