"""PostgreSQL database models and session management."""

import os
import logging
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv('POSTGRES_URL', 'postgresql://user:password@localhost:5432/ragdb')

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    """Document metadata model."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_url = Column(String(500))
    document_type = Column(String(50), nullable=False)  # text, image, document
    metadata = Column(JSON, default={})
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Action(Base):
    """Scheduled action model."""
    __tablename__ = "actions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    action_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False)  # pending, running, completed, failed
    scheduled_time = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskHistory(Base):
    """Task execution history model."""
    __tablename__ = "task_history"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), index=True, nullable=False)
    task_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # in milliseconds
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def close_db():
    """Close database connections."""
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
