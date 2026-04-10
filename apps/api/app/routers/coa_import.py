from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.middleware import get_current_user, security
from app.services.coa_templates import load_template, apply_template
from app.services.csv_importer import import_csv
from app.services.xero_parser import parse_xero_xml

router = APIRouter(prefix="/coa-import", tags=["coa"])


@router.get("/templates")
async def list_templates():
    """List available COA templates."""
    templates = [
        {"id": "saas", "name": "SaaS Startup"},
        {"id": "agency", "name": "Marketing Agency"},
        {"id": "ecommerce", "name": "E-Commerce"},
        {"id": "professional_services", "name": "Professional Services"},
        {"id": "retail", "name": "Retail"},
        {"id": "nonprofit", "name": "Nonprofit"},
        {"id": "manufacturing", "name": "Manufacturing"},
    ]
    return {"templates": templates}


@router.post("/apply-template/{template_name}")
async def apply_coa_template(
    template_name: str,
    client_id: int = Query(...),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Apply a COA template to a client."""
    ctx = await get_current_user(credentials)
    template = load_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    result = apply_template(client_id, ctx.agency_id, template, db)
    return {"message": f"Applied {template_name} template", "accounts_created": result}


@router.post("/csv-import")
async def import_csv_coa(
    client_id: int = Query(...),
    file: UploadFile = File(...),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Import COA from CSV file."""
    ctx = await get_current_user(credentials)
    content = await file.read()
    result = import_csv(client_id, ctx.agency_id, content, db)
    return result


@router.post("/xero-import")
async def import_xero_coa(
    client_id: int = Query(...),
    file: UploadFile = File(...),
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """Import COA from Xero XML export."""
    ctx = await get_current_user(credentials)
    content = await file.read()
    result = parse_xero_xml(client_id, ctx.agency_id, content, db)
    return result
