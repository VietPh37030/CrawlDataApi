"""
API Dependencies
FastAPI dependency injection
"""
from typing import Generator
from ..database import Database, db


def get_db() -> Generator[Database, None, None]:
    """Get database instance"""
    yield db
