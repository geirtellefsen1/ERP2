from fastapi import APIRouter, Depends
from app.auth.middleware import get_current_user, security
from app.schemas.ai import (
    ExtractDocumentRequest,
    ExtractDocumentResponse,
    SuggestGLCodeRequest,
    SuggestGLCodeResponse,
    DetectAnomaliesRequest,
    DetectAnomaliesResponse,
    GenerateNarrativeRequest,
    GenerateNarrativeResponse,
)
from app.services.ai_client import ClaudeClient
from app.services.ai_prompts import (
    document_extraction_prompt,
    gl_coding_prompt,
    anomaly_detection_prompt,
    report_narrative_prompt,
)

router = APIRouter(prefix="/ai", tags=["ai"])


def get_claude_client() -> ClaudeClient:
    return ClaudeClient()


@router.post("/extract-document", response_model=ExtractDocumentResponse)
async def extract_document(
    request: ExtractDocumentRequest,
    credentials=Depends(security),
):
    """Extract structured data from document text using Claude AI."""
    ctx = await get_current_user(credentials)
    client = get_claude_client()
    system_prompt = document_extraction_prompt(request.document_type)
    result = await client.complete(system_prompt, request.document_text)

    return ExtractDocumentResponse(
        extracted_data=result,
        document_type=request.document_type,
    )


@router.post("/suggest-gl-code", response_model=SuggestGLCodeResponse)
async def suggest_gl_code(
    request: SuggestGLCodeRequest,
    credentials=Depends(security),
):
    """Suggest a GL code for a transaction description using Claude AI."""
    ctx = await get_current_user(credentials)
    client = get_claude_client()
    system_prompt = gl_coding_prompt(request.description, request.chart_of_accounts)
    result = await client.complete(system_prompt, request.description)

    return SuggestGLCodeResponse(
        suggestion=result,
        description=request.description,
    )


@router.post("/detect-anomalies", response_model=DetectAnomaliesResponse)
async def detect_anomalies(
    request: DetectAnomaliesRequest,
    credentials=Depends(security),
):
    """Detect anomalies in a set of transactions using Claude AI."""
    ctx = await get_current_user(credentials)
    client = get_claude_client()
    system_prompt = anomaly_detection_prompt(request.transactions_json)
    result = await client.complete(system_prompt, request.transactions_json)

    return DetectAnomaliesResponse(analysis=result)


@router.post("/generate-narrative", response_model=GenerateNarrativeResponse)
async def generate_narrative(
    request: GenerateNarrativeRequest,
    credentials=Depends(security),
):
    """Generate a narrative summary for financial data using Claude AI."""
    ctx = await get_current_user(credentials)
    client = get_claude_client()
    system_prompt = report_narrative_prompt(request.financials_json)
    result = await client.complete(system_prompt, request.financials_json)

    return GenerateNarrativeResponse(narrative=result)
