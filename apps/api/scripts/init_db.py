#!/usr/bin/env python3
"""Initialize database: run migrations and seed development data."""
import os
import sys

# Add the api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from alembic.config import Config
from alembic import command
from app.db.session import SessionLocal
from app.db.seed import seed_database


def init_database():
    # Run Alembic migrations
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied.")

    # Seed development data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    print("Database initialization complete.")


if __name__ == "__main__":
    init_database()
