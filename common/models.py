from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Supported event types"""

    PURCHASE = "purchase"
    USER_SIGNUP = "user_signup"
    PAGE_VIEW = "page_view"
    CUSTOM = "custom"


class EventStatus(str, Enum):
    """Event processing status"""

    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class Event(BaseModel):
    """Event model for ingestion"""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    user_id: Optional[str] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    properties: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        # Remove timezone info to make it naive for PostgreSQL
        if v and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v

    @field_validator("properties")
    @classmethod
    def validate_properties(cls, v):
        if not isinstance(v, dict):
            raise ValueError("properties must be a dictionary")
        return v


class ProcessedEvent(BaseModel):
    """Processed event with enrichment"""

    id: UUID
    event_id: UUID
    event_type: EventType
    user_id: Optional[str]
    timestamp: datetime
    properties: Dict[str, Any]
    processed_at: datetime
    status: EventStatus
    enriched_data: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    error_message: Optional[str] = None


class EventResponse(BaseModel):
    """API response for event submission"""

    event_id: UUID
    status: str
    message: str
    received_at: datetime


class HealthCheck(BaseModel):
    """Health check response"""

    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str = "1.0.0"


class MetricsSnapshot(BaseModel):
    """System metrics snapshot"""

    events_received: int
    events_processed: int
    events_failed: int
    queue_depth: int
    avg_processing_time_ms: float
    timestamp: datetime
