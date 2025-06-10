"""
Database connection and session management for HTS Tariff Calculator
"""
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Generator

from .models import Base

# Database file path
DATABASE_DIR = Path(__file__).parent.parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_FILE = DATABASE_DIR / "hts_tariff.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"


# SQLAlchemy engine configuration for SQLite
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,  # Allow multi-threading
        "timeout": 30  # 30 second timeout for locked database
    },
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields database sessions.
    To be used with FastAPI's Depends()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for direct use
    Remember to close the session when done
    """
    return SessionLocal()


class DatabaseManager:
    """Database manager for handling connections and operations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def reset_database(self):
        """Reset the entire database (development use only)"""
        self.drop_tables()
        self.create_tables()
    
    def get_raw_connection(self):
        """Get raw SQLite connection for direct SQL operations"""
        return sqlite3.connect(DATABASE_FILE)
    
    def execute_raw_sql(self, sql: str, params: tuple = None):
        """Execute raw SQL (use with caution)"""
        with self.get_raw_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor.fetchall()


# Global database manager instance
db_manager = DatabaseManager()


def init_database():
    """Initialize the database and create tables"""
    print(f"Initializing SQLite database at: {DATABASE_FILE}")
    db_manager.create_tables()
    print("Database initialized successfully!")


if __name__ == "__main__":
    # For testing - create tables
    init_database() 