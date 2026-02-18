# Testing Guide

Comprehensive testing strategies for EventFlow.

## Testing Philosophy

EventFlow uses a multi-layered testing approach:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions
3. **End-to-End Tests** - Test complete workflows
4. **Load Tests** - Test performance and scalability
5. **Manual Tests** - Interactive testing via API

## Test Structure

```
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   └── test_models.py          # Model validation tests
└── integration/
    ├── __init__.py
    └── test_end_to_end.py      # Full workflow tests
```

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Start services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test
pytest tests/unit/test_models.py::test_event_creation
```

### Run by Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Tests matching pattern
pytest -k "test_event"
```

## Unit Tests

Unit tests verify individual components work correctly in isolation.

### Model Tests

Test Pydantic models and validation:

```python
# tests/unit/test_models.py

def test_event_creation():
    """Test creating a valid event"""
    event = Event(
        event_type=EventType.PURCHASE,
        user_id="user123",
        properties={"amount": 99.99}
    )
    assert event.event_type == EventType.PURCHASE
    assert event.user_id == "user123"
    assert event.properties["amount"] == 99.99

def test_event_validation():
    """Test event validation"""
    with pytest.raises(ValidationError):
        Event(
            event_type="invalid_type",  # Invalid enum
            user_id="user123"
        )

def test_event_defaults():
    """Test default values"""
    event = Event(event_type=EventType.PAGE_VIEW)
    assert event.event_id is not None
    assert event.timestamp is not None
    assert event.properties == {}
```

### Running Unit Tests

```bash
pytest tests/unit/ -v
```

## Integration Tests

Integration tests verify components work together correctly.

### End-to-End Test

Test complete event flow from API to database:

```python
# tests/integration/test_end_to_end.py

@pytest.mark.asyncio
async def test_event_flow():
    """Test complete event processing flow"""
    
    # 1. Submit event to API
    event_data = {
        "event_type": "purchase",
        "user_id": "test_user",
        "properties": {"amount": 99.99}
    }
    
    response = await client.post("/events", json=event_data)
    assert response.status_code == 202
    
    event_id = response.json()["event_id"]
    
    # 2. Wait for processing
    await asyncio.sleep(2)
    
    # 3. Verify in database
    async with get_db() as session:
        result = await session.execute(
            select(ProcessedEventDB).where(
                ProcessedEventDB.event_id == event_id
            )
        )
        processed = result.scalar_one_or_none()
        
        assert processed is not None
        assert processed.status == "completed"
        assert processed.enriched_data is not None
```

### Running Integration Tests

```bash
# Ensure services are running
docker-compose up -d

# Run integration tests
pytest tests/integration/ -v

# Run with logs
pytest tests/integration/ -v -s
```

## Load Testing

Test system performance under load.

### Using Load Test Script

```bash
# Install dependencies
pip install -r requirements.txt

# Run load test
python scripts/load_test.py --events 10000 --rate 100

# Options:
# --events: Total number of events to send
# --rate: Events per second
# --workers: Number of concurrent workers
```

### Load Test Output

```
Starting load test...
Target: 10000 events at 100 events/sec
Workers: 10

Progress: [████████████████████] 100%
Completed: 10000/10000

Results:
  Duration: 102.5 seconds
  Actual Rate: 97.6 events/sec
  Success: 9998 (99.98%)
  Failed: 2 (0.02%)
  
Latency:
  P50: 45ms
  P95: 89ms
  P99: 156ms
  Max: 342ms
```

### Performance Targets

- **Throughput:** 1000+ events/second
- **Latency P95:** < 100ms
- **Success Rate:** > 99.9%
- **Queue Depth:** < 1000 under normal load

### Monitoring During Load Tests

```bash
# Terminal 1: Run load test
python scripts/load_test.py --events 10000 --rate 100

# Terminal 2: Monitor metrics
python scripts/monitor.py

# Terminal 3: Watch logs
docker-compose logs -f worker

# Terminal 4: Check resources
docker stats
```

## Manual Testing

### Using Interactive API Docs

1. Open http://localhost:8000/docs
2. Expand `POST /events`
3. Click "Try it out"
4. Modify request body
5. Click "Execute"
6. View response

### Using cURL

```bash
# Send purchase event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "purchase",
    "user_id": "user123",
    "properties": {"amount": 99.99, "product": "Widget"}
  }'

# Send page view event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "page_view",
    "user_id": "user456",
    "properties": {"page": "/home", "referrer": "google"}
  }'

# Check health
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/metrics/summary
```

### Using Python Producer Script

```bash
# Send 10 events
python scripts/producer.py --count 10

# Send 100 events at 10/sec
python scripts/producer.py --count 100 --rate 10

# Send events continuously
python scripts/producer.py --count 10000 --rate 50
```

### Using PowerShell Script (Windows)

```powershell
.\send_test_event.ps1
```

## Testing Scenarios

### Happy Path

Test normal event processing:

```bash
# 1. Send valid event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "purchase", "user_id": "user123", "properties": {"amount": 99.99}}'

# 2. Check it was processed
docker-compose exec postgres psql -U eventflow -d eventflow \
  -c "SELECT * FROM processed_events ORDER BY processed_at DESC LIMIT 1;"
```

### Duplicate Detection

Test idempotency:

```bash
# Send same event twice (same event_id)
EVENT_ID="123e4567-e89b-12d3-a456-426614174000"

curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d "{\"event_id\": \"$EVENT_ID\", \"event_type\": \"purchase\", \"user_id\": \"user123\", \"properties\": {\"amount\": 99.99}}"

# Send again
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d "{\"event_id\": \"$EVENT_ID\", \"event_type\": \"purchase\", \"user_id\": \"user123\", \"properties\": {\"amount\": 99.99}}"

# Check only one processed
docker-compose exec postgres psql -U eventflow -d eventflow \
  -c "SELECT COUNT(*) FROM processed_events WHERE event_id = '$EVENT_ID';"
# Should return 1
```

### Invalid Event

Test validation:

```bash
# Send invalid event (missing required field)
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
# Should return 422 Unprocessable Entity

# Send invalid event type
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "invalid", "user_id": "user123"}'
# Should return 422 Unprocessable Entity
```

### Business Logic Validation

Test domain-specific validation:

```bash
# Purchase without amount (should fail)
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "purchase", "user_id": "user123", "properties": {}}'

# Check DLQ
docker-compose exec postgres psql -U eventflow -d eventflow \
  -c "SELECT * FROM failed_events ORDER BY failed_at DESC LIMIT 1;"
```

### Worker Failure Recovery

Test fault tolerance:

```bash
# 1. Send events
python scripts/producer.py --count 100

# 2. Kill a worker
docker-compose kill worker

# 3. Check messages are redelivered
docker-compose logs -f worker

# 4. Restart worker
docker-compose up -d worker

# 5. Verify all events processed
curl http://localhost:8000/metrics/summary
```

### Database Failure

Test retry logic:

```bash
# 1. Send events
python scripts/producer.py --count 10 &

# 2. Stop database
docker-compose stop postgres

# 3. Watch worker logs (should see retries)
docker-compose logs -f worker

# 4. Restart database
docker-compose start postgres

# 5. Verify events eventually processed
docker-compose exec postgres psql -U eventflow -d eventflow \
  -c "SELECT COUNT(*) FROM processed_events;"
```

### Scaling Test

Test horizontal scaling:

```bash
# 1. Start with 1 worker
docker-compose up -d --scale worker=1

# 2. Send load
python scripts/load_test.py --events 1000 --rate 50 &

# 3. Monitor queue depth
watch -n 1 'curl -s http://localhost:8000/metrics/summary | jq .queue_length'

# 4. Scale to 5 workers
docker-compose up -d --scale worker=5

# 5. Watch queue drain faster
```

## Monitoring Tests

### Check Metrics

```bash
# Prometheus metrics
curl http://localhost:9090/api/v1/query?query=events_processed_total

# API metrics
curl http://localhost:8000/metrics/summary

# Python monitor script
python scripts/monitor.py
```

### Check Logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f worker

# Grep for errors
docker-compose logs worker | grep ERROR

# Follow with timestamps
docker-compose logs -f --timestamps worker
```

### Check Database

```bash
# Connect to database
docker-compose exec postgres psql -U eventflow -d eventflow

# Count processed events
SELECT COUNT(*) FROM processed_events;

# Count failed events
SELECT COUNT(*) FROM failed_events;

# Recent events
SELECT event_id, event_type, processed_at 
FROM processed_events 
ORDER BY processed_at DESC 
LIMIT 10;

# Failed events with errors
SELECT event_id, error_message, failed_at 
FROM failed_events 
ORDER BY failed_at DESC 
LIMIT 10;

# Exit
\q
```

## Test Data Cleanup

### Reset Database

```bash
# Stop services
docker-compose down

# Remove volumes (deletes data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Clear Specific Tables

```bash
docker-compose exec postgres psql -U eventflow -d eventflow

# Clear processed events
TRUNCATE processed_events;

# Clear failed events
TRUNCATE failed_events;

# Clear raw events
TRUNCATE raw_events;

# Exit
\q
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Start services
      run: docker-compose up -d
    
    - name: Wait for services
      run: sleep 30
    
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Best Practices

### Test Isolation

- Each test should be independent
- Clean up test data after tests
- Use unique identifiers for test data
- Don't rely on test execution order

### Test Coverage

- Aim for >80% code coverage
- Test happy paths and error cases
- Test edge cases and boundary conditions
- Test concurrent scenarios

### Performance Testing

- Run load tests regularly
- Monitor resource usage
- Test with realistic data volumes
- Test scaling scenarios

### Integration Testing

- Test with real dependencies
- Use Docker for consistent environments
- Test failure scenarios
- Test recovery mechanisms

## Troubleshooting Tests

### Tests Failing

```bash
# Check services are running
docker-compose ps

# Check service health
curl http://localhost:8000/health

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Clean slate
docker-compose down -v
docker-compose up -d
```

### Slow Tests

```bash
# Run specific tests
pytest tests/unit/test_models.py

# Run in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"
```

### Flaky Tests

- Add retries for network operations
- Increase timeouts
- Add explicit waits
- Check for race conditions

## Summary

EventFlow provides comprehensive testing at multiple levels:

- **Unit tests** for component validation
- **Integration tests** for workflow verification
- **Load tests** for performance validation
- **Manual tests** for interactive exploration

Run tests regularly to ensure system reliability and catch regressions early.
