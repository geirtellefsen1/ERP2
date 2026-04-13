"""
Database session factory for FastAPI dependency injection.

Usage in routers:
    from app.database import get_db
    def my_route(db: Session = Depends(get_db)):
        ...

Do NOT decorate get_db with @contextmanager — FastAPI expects a plain
generator function for its dependency injection machinery. The decorator
wraps the function so Depends() receives a _GeneratorContextManager object
instead of the yielded Session, which breaks every router.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url.replace("+asyncpg", ""),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that yields a database session and closes it after the
    request completes. Plain generator — do not add @contextmanager.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
