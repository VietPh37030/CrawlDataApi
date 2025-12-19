"""
Pydantic Schemas for API Request/Response
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Crawl task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StoryStatus(str, Enum):
    """Story completion status"""
    ONGOING = "ongoing"
    COMPLETED = "completed"


# ========== Request Schemas ==========

class CrawlRequest(BaseModel):
    """Request to start a crawl job"""
    url: str = Field(..., description="Story URL to crawl", example="https://truyenfull.vision/tam-quoc-dien-nghia/")
    crawl_chapters: bool = Field(default=True, description="Whether to crawl chapter content")


class StorySearchRequest(BaseModel):
    """Request to search stories"""
    query: Optional[str] = None
    genre: Optional[str] = None
    status: Optional[StoryStatus] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ========== Response Schemas ==========

class StoryBase(BaseModel):
    """Base story schema"""
    slug: str
    title: str
    author: Optional[str] = None
    description: Optional[str] = None
    genres: List[str] = []
    status: StoryStatus = StoryStatus.ONGOING
    total_chapters: int = 0
    cover_url: Optional[str] = None
    source_url: str


class StoryResponse(StoryBase):
    """Story response with metadata"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StoryListResponse(BaseModel):
    """Paginated story list"""
    items: List[StoryResponse]
    total: int
    limit: int
    offset: int


class ChapterBase(BaseModel):
    """Base chapter schema"""
    chapter_number: int
    title: str
    content: Optional[str] = None
    source_url: str


class ChapterResponse(ChapterBase):
    """Chapter response"""
    id: str
    story_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChapterListResponse(BaseModel):
    """Chapter list response"""
    items: List[ChapterResponse]
    total: int


class TaskResponse(BaseModel):
    """Crawl task response"""
    id: str
    story_url: str
    status: TaskStatus
    progress: int = 0
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CrawlResponse(BaseModel):
    """Response after starting a crawl job"""
    message: str
    task_id: str
    status: TaskStatus


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    version: str = "1.0.0"
    timestamp: datetime
