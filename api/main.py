import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from common.config import settings
from common.database import RawEvent, check_db_health, get_db, init_db
from common.logging_config import setup_logging
from common.metrics import events_received_total, start_metrics_server
from common.models import Event, EventResponse, HealthCheck
from common.redis_client import redis_client

# Setup logging
logger = setup_logging("api", settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting API service")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Connect to Redis
    await redis_client.connect()
    logger.info("Connected to Redis")

    # Start metrics server
    start_metrics_server(settings.metrics_port)
    logger.info(f"Metrics server started on port {settings.metrics_port}")

    yield

    # Shutdown
    logger.info("Shutting down API service")
    await redis_client.disconnect()


app = FastAPI(
    title="EventFlow API",
    description="Distributed Event Processing System",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""

    # Check dependencies
    db_healthy = await check_db_health()
    redis_healthy = await redis_client.check_health()

    services = {
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": "healthy" if redis_healthy else "unhealthy",
    }

    overall_status = (
        "healthy" if all(s == "healthy" for s in services.values()) else "unhealthy"
    )

    status_code = (
        status.HTTP_200_OK
        if overall_status == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": services,
            "version": "1.0.0",
        },
    )


@app.post("/events", response_model=EventResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_event(event: Event):
    """Submit event for processing"""

    try:
        logger.info(
            "Event received",
            extra={
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "correlation_id": str(event.event_id),
            },
        )

        # Store raw event in database
        async with get_db() as session:
            raw_event = RawEvent(
                event_id=event.event_id,
                payload=event.model_dump(mode="json"),
                received_at=event.timestamp,
            )
            session.add(raw_event)
            await session.flush()

        # Publish to Redis stream
        message_id = await redis_client.publish_event(event.model_dump(mode="json"))

        # Update metrics
        events_received_total.labels(event_type=event.event_type).inc()

        logger.info(
            "Event published to queue",
            extra={
                "event_id": str(event.event_id),
                "message_id": message_id,
                "correlation_id": str(event.event_id),
            },
        )

        return EventResponse(
            event_id=event.event_id,
            status="accepted",
            message="Event accepted for processing",
            received_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(
            f"Failed to process event: {str(e)}",
            extra={
                "event_id": str(event.event_id),
                "error": str(e),
                "correlation_id": str(event.event_id),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process event",
        )


@app.get("/metrics/summary")
async def get_metrics_summary() -> Dict:
    """Get metrics summary"""

    try:
        queue_length = await redis_client.get_stream_length()
        pending_count = await redis_client.get_pending_count()

        return {
            "queue_length": queue_length,
            "pending_messages": pending_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics",
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "EventFlow API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.api_host, port=settings.api_port, reload=False
    )
