from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import get_db
from app.models import User as UserModel
from app.schemas import UserCreate, User as UserSchema

router = APIRouter(prefix="/api/v1/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


@router.get("", response_model=list[UserSchema])
def list_users(agency_id: int = Query(...), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(UserModel).filter(UserModel.agency_id == agency_id).offset(skip).limit(limit).all()


@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = UserModel(
        **data.model_dump(exclude={"password"}),
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
