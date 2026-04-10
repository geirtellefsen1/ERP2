from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Agency
from app.schemas import AgencyCreate, AgencyUpdate, Agency

router = APIRouter(prefix="/api/v1/agencies", tags=["agencies"])


@router.get("", response_model=list[Agency])
def list_agencies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Agency).offset(skip).limit(limit).all()


@router.post("", response_model=Agency, status_code=status.HTTP_201_CREATED)
def create_agency(data: AgencyCreate, db: Session = Depends(get_db)):
    existing = db.query(Agency).filter(Agency.slug == data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agency slug already exists")
    agency = Agency(**data.model_dump())
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


@router.get("/{agency_id}", response_model=Agency)
def get_agency(agency_id: int, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency


@router.patch("/{agency_id}", response_model=Agency)
def update_agency(agency_id: int, data: AgencyUpdate, db: Session = Depends(get_db)):
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(agency, key, value)
    db.commit()
    db.refresh(agency)
    return agency
