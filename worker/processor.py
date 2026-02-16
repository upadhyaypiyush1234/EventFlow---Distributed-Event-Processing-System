import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_exponential

from common.config import settings
from common.database import FailedEvent, ProcessedEventDB, get_db
from common.logging_config import CorrelationIdFilter, setup_logging
from common.metrics import (
    event_processing_duration,
    events_duplicate_total,
    events_failed_total,
    events_processed_total,
)
from common.models import Event, EventStatus

logger = setup_logging("worker", settings.log_level)


class EventProcessor:
    """Process events with validation, enrichment, and error handling"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.logger = logger
    
    async def process_event(self, event_data: Dict[str, Any], message_id: str) -> bool:
        """
        Process a single event
        
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        start_time = datetime.utcnow()
        event_id = None
        
        try:
            # Parse event
            event = Event(**event_data)
            event_id = event.event_id
            
            # Add correlation ID to logs
            correlation_filter = CorrelationIdFilter(str(event_id))
            self.logger.addFilter(correlation_filter)
            
            self.logger.info(
                f"Processing event",
                extra={
                    "event_id": str(event_id),
                    "event_type": event.event_type,
                    "worker_id": self.worker_id,
                    "message_id": message_id
                }
            )
            
            # Check for duplicates (idempotency)
            if await self._is_duplicate(event_id):
                self.logger.info(
                    f"Duplicate event detected, skipping",
                    extra={"event_id": str(event_id)}
                )
                events_duplicate_total.labels(event_type=event.event_type).inc()
                return True
            
            # Validate event
            await self._validate_event(event)
            
            # Enrich event
            enriched_data = await self._enrich_event(event)
            
            # Persist processed event
            await self._persist_event(event, enriched_data)
            
            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            event_processing_duration.labels(event_type=event.event_type).observe(processing_time)
            events_processed_total.labels(event_type=event.event_type).inc()
            
            self.logger.info(
                f"Event processed successfully",
                extra={
                    "event_id": str(event_id),
                    "processing_time_ms": processing_time * 1000,
                    "worker_id": self.worker_id
                }
            )
            
            self.logger.removeFilter(correlation_filter)
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to process event: {str(e)}",
                extra={
                    "event_id": str(event_id) if event_id else "unknown",
                    "error": str(e),
                    "worker_id": self.worker_id
                },
                exc_info=True
            )
            
            # Move to dead letter queue
            await self._move_to_dlq(event_data, str(e))
            
            if event_id:
                event_type = event_data.get('event_type', 'unknown')
                events_failed_total.labels(
                    event_type=event_type,
                    error_type=type(e).__name__
                ).inc()
            
            return False
    
    async def _is_duplicate(self, event_id: UUID) -> bool:
        """Check if event has already been processed"""
        async with get_db() as session:
            result = await session.execute(
                select(ProcessedEventDB).where(ProcessedEventDB.event_id == event_id)
            )
            return result.scalar_one_or_none() is not None
    
    async def _validate_event(self, event: Event):
        """Validate event data"""
        # Business logic validation
        if event.event_type == "purchase":
            if not event.properties.get("amount"):
                raise ValueError("Purchase events must have an amount")
            
            amount = event.properties["amount"]
            if not isinstance(amount, (int, float)) or amount <= 0:
                raise ValueError("Purchase amount must be positive")
        
        if event.event_type == "user_signup":
            if not event.user_id:
                raise ValueError("User signup events must have a user_id")
        
        # Timestamp validation
        now = datetime.utcnow()
        if event.timestamp > now:
            raise ValueError("Event timestamp cannot be in the future")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _enrich_event(self, event: Event) -> Dict[str, Any]:
        """Enrich event with additional data"""
        enriched = {
            "processed_by": self.worker_id,
            "processing_timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add event-specific enrichment
        if event.event_type == "purchase":
            amount = event.properties.get("amount", 0)
            enriched["category"] = "high_value" if amount > 1000 else "standard"
        
        if event.event_type == "page_view":
            enriched["session_start"] = event.timestamp.isoformat()
        
        # Simulate external API call (with retry)
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return enriched
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _persist_event(self, event: Event, enriched_data: Dict[str, Any]):
        """Persist processed event to database"""
        async with get_db() as session:
            processed_event = ProcessedEventDB(
                event_id=event.event_id,
                event_type=event.event_type,
                user_id=event.user_id,
                timestamp=event.timestamp,
                properties=event.properties,
                processed_at=datetime.utcnow(),
                status=EventStatus.COMPLETED.value,
                enriched_data=enriched_data,
                retry_count=0
            )
            session.add(processed_event)
            await session.flush()
    
    async def _move_to_dlq(self, event_data: Dict[str, Any], error_message: str):
        """Move failed event to dead letter queue"""
        try:
            async with get_db() as session:
                failed_event = FailedEvent(
                    event_id=UUID(event_data.get("event_id")),
                    payload=event_data,
                    error_message=error_message,
                    failed_at=datetime.utcnow(),
                    retry_count=0
                )
                session.add(failed_event)
                await session.flush()
            
            self.logger.info(
                "Event moved to DLQ",
                extra={
                    "event_id": event_data.get("event_id"),
                    "error": error_message
                }
            )
        except Exception as e:
            self.logger.error(
                f"Failed to move event to DLQ: {str(e)}",
                exc_info=True
            )
