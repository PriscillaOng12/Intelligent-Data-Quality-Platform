from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for ORM models
Base = declarative_base()

# Metadata for table creation
metadata = MetaData()


async def create_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def get_db() -> Generator:
    """Get database session for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def check_db_connection():
    """Check database connectivity"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


class DatabaseManager:
    """Database manager for handling connections and transactions"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    async def execute_query(self, query: str, params: dict = None):
        """Execute raw SQL query"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(query, params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def health_check(self):
        """Perform database health check"""
        try:
            await self.execute_query("SELECT 1")
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global database manager instance
db_manager = DatabaseManager()
