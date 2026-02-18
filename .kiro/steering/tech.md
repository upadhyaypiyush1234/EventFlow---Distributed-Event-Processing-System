# Technology Stack

## Core Technologies

- **Language**: Python 3.11+
- **API Framework**: FastAPI (async web framework)
- **Message Queue**: Redis Streams (consumer groups, at-least-once delivery)
- **Database**: PostgreSQL 15 (with asyncpg driver)
- **ORM**: SQLAlchemy 2.0 (async mode)
- **Containerization**: Docker & Docker Compose
- **Monitoring**: Prometheus + Grafana

## Key Libraries

- `fastapi` - Modern async web framework with auto-generated OpenAPI docs
- `uvicorn` - ASGI server for FastAPI
- `pydantic` - Data validation and settings management
- `redis` - Redis client for streams and pub/sub
- `sqlalchemy[asyncio]` - Async ORM for database operations
- `asyncpg` - High-performance async PostgreSQL driver
- `tenacity` - Retry logic with exponential backoff
- `python-json-logger` - Structured JSON logging
- `prometheus-client` - Metrics export
- `httpx` - Async HTTP client

## Code Style

- **Formatter**: Black (line length: 88)
- **Target**: Python 3.11+
- **Async**: asyncio throughout (non-blocking I/O)
- **Type Hints**: Use Pydantic models for validation
- **Logging**: Structured JSON with correlation IDs

## Common Commands

### Development

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Check service status
docker-compose ps

# Scale workers
docker-compose up -d --scale worker=5

# Rebuild after code changes
docker-compose up -d --build
```

### Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests with coverage
pytest --cov=. --cov-report=html

# Send test event
python scripts/producer.py --count 10

# Load testing
python scripts/load_test.py --events 1000 --rate 100

# Monitor system
python scripts/monitor.py
```

### Database

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U eventflow -d eventflow

# Run migrations (manual SQL in scripts/init_db.sql)
docker-compose exec postgres psql -U eventflow -d eventflow -f /docker-entrypoint-initdb.d/init.sql
```

### Monitoring

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Metrics Summary: http://localhost:8000/metrics/summary
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Architecture Patterns

- **Async/Await**: All I/O operations are non-blocking
- **Connection Pooling**: Database connections are pooled for efficiency
- **Consumer Groups**: Redis Streams consumer groups for load balancing
- **Idempotency**: Event IDs prevent duplicate processing
- **Retry Logic**: Exponential backoff with tenacity decorator
- **Graceful Shutdown**: Signal handlers ensure clean worker shutdown
- **Structured Logging**: JSON logs with correlation IDs for tracing
