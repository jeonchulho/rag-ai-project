"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class SearchType(str, Enum):
    """Type of search to perform."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    ALL = "all"


class ActionType(str, Enum):
    """Type of action to execute."""
    EMAIL = "email"
    SUMMARIZE = "summarize"
    NOTIFY = "notify"


# ========== Search Models ==========

class SearchRequest(BaseModel):
    """Request for basic search."""
    query: str = Field(..., description="Search query text")
    search_type: SearchType = Field(default=SearchType.ALL, description="Type of search")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")


class SearchResult(BaseModel):
    """Individual search result."""
    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    document_type: str = Field(..., description="Type of document")


class SearchResponse(BaseModel):
    """Response for search queries."""
    results: List[SearchResult] = Field(default_factory=list, description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")
    search_type: str = Field(..., description="Type of search performed")
    execution_time: float = Field(..., description="Query execution time in seconds")


class NaturalLanguageRequest(BaseModel):
    """Request for natural language query processing."""
    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class NaturalLanguageResponse(BaseModel):
    """Response for natural language queries."""
    intent: str = Field(..., description="Detected intent")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    search_results: Optional[List[SearchResult]] = Field(default=None, description="Search results if applicable")
    summary: Optional[str] = Field(default=None, description="Generated summary if requested")
    scheduled_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Scheduled actions")
    response_text: str = Field(..., description="Human-readable response")
    execution_time: float = Field(..., description="Total execution time in seconds")


# ========== Upload Models ==========

class UploadResponse(BaseModel):
    """Response for file upload."""
    document_id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")


# ========== Action Models ==========

class EmailAction(BaseModel):
    """Email action details."""
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    scheduled_time: Optional[datetime] = Field(default=None, description="Scheduled send time")


class ActionRequest(BaseModel):
    """Request to schedule an action."""
    action_type: ActionType = Field(..., description="Type of action")
    parameters: Dict[str, Any] = Field(..., description="Action parameters")
    scheduled_time: Optional[datetime] = Field(default=None, description="When to execute")


class ActionResponse(BaseModel):
    """Response for action scheduling."""
    task_id: str = Field(..., description="Unique task ID")
    action_type: str = Field(..., description="Type of action")
    status: str = Field(..., description="Task status")
    scheduled_time: Optional[datetime] = Field(default=None, description="Scheduled execution time")
    message: str = Field(..., description="Status message")


class TaskStatus(BaseModel):
    """Status of a background task."""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Current status")
    result: Optional[Any] = Field(default=None, description="Task result if completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(..., description="Task creation time")
    updated_at: datetime = Field(..., description="Last update time")


# ========== Health Check Models ==========

class ServiceHealth(BaseModel):
    """Health status of a service."""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Status: healthy, unhealthy, degraded")
    response_time: Optional[float] = Field(default=None, description="Response time in ms")
    details: Optional[str] = Field(default=None, description="Additional details")


class HealthResponse(BaseModel):
    """Overall system health response."""
    status: str = Field(..., description="Overall status")
    version: str = Field(..., description="API version")
    instance_id: str = Field(..., description="Instance identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    services: List[ServiceHealth] = Field(default_factory=list, description="Individual service health")
