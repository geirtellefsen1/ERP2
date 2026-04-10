from pydantic import BaseModel
from typing import Optional


class ExtractDocumentRequest(BaseModel):
    document_text: str
    document_type: str = "invoice"


class ExtractDocumentResponse(BaseModel):
    extracted_data: str
    document_type: str


class SuggestGLCodeRequest(BaseModel):
    description: str
    chart_of_accounts: Optional[str] = None


class SuggestGLCodeResponse(BaseModel):
    suggestion: str
    description: str


class DetectAnomaliesRequest(BaseModel):
    transactions_json: str


class DetectAnomaliesResponse(BaseModel):
    analysis: str


class GenerateNarrativeRequest(BaseModel):
    financials_json: str


class GenerateNarrativeResponse(BaseModel):
    narrative: str
