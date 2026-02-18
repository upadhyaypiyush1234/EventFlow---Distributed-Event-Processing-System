# Project Structure

## Directory Layout

```
eventflow/
├── api/                    # FastAPI service (event ingestion)
│   ├── __init__.py
│   └── main.py            # API endpoints, health checks, metrics
├── worker/                 # Event processing workers
│   ├── __init__.py
│   ├── main.py            # Worker lifecycle, message consumption
│   └── processor.py       # Event processing logic
├── common/                 # Shared modules
│   ├── __init__.py
│   ├── config.py          # Settings and environment variables
│   ├── database.py        # SQLAlchemy models and DB utilities
│   ├── logging_config.py  # Structured JSON logging setup
│   ├── metrics.py         # Prometheus metrics definitions
│   ├── models.py          # Pydantic models for validation
│   └── redis_client.py    # Redis Streams client wrapper
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # End-to-end integration tests
├── scripts/                # Utility scripts
│   ├── init_db.sql        # Database schema initialization
│   ├── producer.py        # Test event generator
│   ├── load_test.py       # Load testing script
│   └── monitor.py         # System monitoring script
├── config/                 # Configuration files
│   ├── prometheus.yml     # Prometheus scrape config
│   └── grafana-datasources.yml
├── docker-compose.yml      # Service orchestration
├── Dockerfile.api          # API service container
├── Dockerfile.worker       # Worker service container
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Black formatter config
└── pytest.ini             # Pytest configuration
```

## Module Organization

### API Service (`api/`)
- Single-file FastAPI application
- Handles event ingestion, validation, and queueing
- Provides health checks and metrics endpoints
- Stores raw events for audit trail
- Publishes to Redis Streams

### Worker Service (`worker/`)
- `main.py`: Worker lifecycle, signal handling, message consumption loop
- `processor.py`: Core event processing logic (validation, enrichment, persistence)
- Consumes from Redis Streams consumer group
- Implements idempotency checks and retry logic

### Common Modules (`common/`)
- `config.py`: Centralized settings using pydantic-settings
- `database.py`: SQLAlchemy async engine, session management, table models
- `models.py`: Pydantic models for API validation and data transfer
- `redis_client.py`: Redis Streams wrapper (publish, consume, acknowledge)
- `logging_config.py`: JSON logger with correlation ID support
- `metrics.py`: Prometheus counter/gauge/histogram definitions

### Database Schema
Three main tables (defined in `common/database.py`):
- `raw_events`: Audit trail of all incoming events
- `processed_events`: Successfully processed events with enrichment
- `failed_events`: Dead letter queue for permanent failures

## Key Conventions

### Async Patterns
- All I/O operations use `async`/`await`
- Database sessions use async context managers
- Redis operations are async
- Worker processing loop is async

### Error Handling
- API returns 202 Accepted for valid events (async processing)
- Workers retry transient failures with exponential backoff
- Permanent failures move to dead letter queue
- All errors logged with correlation IDs

### Logging
- Structured JSON format for all logs
- Include `correlation_id` (event_id) for tracing
- Log levels: DEBUG, INFO, WARNING, ERROR
- Extra context in `extra` dict

### Metrics
- Prometheus metrics exposed on separate port (9091)
- Counter: `events_received_total`, `events_processed_total`, `events_failed_total`
- Gauge: `queue_depth`, `active_workers`
- Histogram: `event_processing_duration`

### Configuration
- Environment variables for all config (12-factor app)
- Defaults in `common/config.py`
- Override via `.env` file or docker-compose environment

### Testing
- Unit tests in `tests/unit/` (test individual functions)
- Integration tests in `tests/integration/` (test full flow)
- Use pytest fixtures for database and Redis setup
- Mock external dependencies in unit tests

## Data Flow

1. Client → API (`POST /events`)
2. API → PostgreSQL (`raw_events` table)
3. API → Redis Streams (`event_queue` stream)
4. Worker ← Redis Streams (consumer group)
5. Worker → PostgreSQL (`processed_events` or `failed_events`)
6. Worker → Redis (acknowledge message)

## Adding New Features

### New Event Type
1. Add to `EventType` enum in `common/models.py`
2. Add validation logic in `worker/processor.py`
3. Update tests

### New Endpoint
1. Add route in `api/main.py`
2. Define request/response models in `common/models.py`
3. Add integration test

### New Metric
1. Define in `common/metrics.py`
2. Instrument code where metric should be updated
3. Update Prometheus/Grafana dashboards
