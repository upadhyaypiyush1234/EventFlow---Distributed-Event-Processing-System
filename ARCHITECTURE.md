# EventFlow Architecture

## System Overview

EventFlow is a distributed event processing system designed for high throughput, fault tolerance, and observability. It follows a queue-based architecture with async processing.

## Architecture Diagram

```
┌─────────────┐
│  Producers  │
│  (Clients)  │
└──────┬──────┘
       │ HTTP POST
       ▼
┌─────────────────────────────────────────┐
│           FastAPI Service               │
│  ┌─────────────────────────────────┐   │
│  │  /events - Event Ingestion      │   │
│  │  /health - Health Check         │   │
│  │  /metrics/summary - Stats       │   │
│  └─────────────────────────────────┘   │
└──────┬──────────────────────┬───────────┘
       │                      │
       │ Store Raw           │ Publish
       ▼                      ▼
┌─────────────┐      ┌──────────────────┐
│ PostgreSQL  │      │  Redis Streams   │
│ (raw_events)│      │  (event_queue)   │
└─────────────┘      └────────┬─────────┘
                              │
                              │ Consumer Group
                              ▼
                     ┌──────────────────┐
                     │  Worker Pool     │
                     │  (Scalable)      │
                     │  ┌────────────┐  │
                     │  │ Worker 1   │  │
                     │  │ Worker 2   │  │
                     │  │ Worker N   │  │
                     │  └────────────┘  │
                     └────┬────────┬────┘
                          │        │
              Process     │        │ Failed
              Success     │        │
                          ▼        ▼
                   ┌──────────┐  ┌──────────┐
                   │PostgreSQL│  │PostgreSQL│
                   │processed │  │  failed  │
                   │ _events  │  │ _events  │
                   └──────────┘  └──────────┘
                          │
                          │
                          ▼
                   ┌──────────────────┐
                   │  Observability   │
                   │  ┌────────────┐  │
                   │  │Prometheus  │  │
                   │  │Grafana     │  │
                   │  │Logs        │  │
                   │  └────────────┘  │
                   └──────────────────┘
```

## Components

### 1. API Service (FastAPI)

**Responsibilities:**
- Accept incoming events via HTTP
- Validate event schema
- Store raw events in PostgreSQL
- Publish events to Redis Streams
- Provide health checks and metrics

**Key Features:**
- Async I/O for high throughput
- Auto-generated OpenAPI documentation
- Structured logging with correlation IDs
- Prometheus metrics export

**Endpoints:**
- `POST /events` - Submit event for processing
- `GET /health` - Health check (includes dependency status)
- `GET /metrics/summary` - Queue and processing stats
- `GET /` - Service info

### 2. Redis Streams (Message Queue)

**Why Redis Streams?**
- Consumer groups for load balancing
- At-least-once delivery semantics
- Automatic message redelivery on failure
- Simpler than Kafka for demos
- Easy migration path to Kafka if needed

**Configuration:**
- Stream name: `event_queue`
- Consumer group: `event_processors`
- Pending message timeout: 60 seconds
- Max retries before DLQ: 3

### 3. Worker Pool (Event Processors)

**Responsibilities:**
- Consume events from Redis Streams
- Validate business logic
- Enrich events with additional data
- Persist processed events
- Handle failures and retries

**Processing Pipeline:**
1. Consume message from queue
2. Check for duplicates (idempotency)
3. Validate event data
4. Enrich with additional context
5. Persist to database
6. Acknowledge message
7. Update metrics

**Fault Tolerance:**
- Idempotency checks prevent duplicate processing
- Retry logic with exponential backoff
- Dead letter queue for permanent failures
- Graceful shutdown with message acknowledgment

### 4. PostgreSQL (Persistence)

**Tables:**

**raw_events:**
- Stores all incoming events as received
- Used for audit trail and replay
- Minimal processing overhead

**processed_events:**
- Stores successfully processed events
- Includes enrichment data
- Used for analytics and queries

**failed_events:**
- Dead letter queue for failed events
- Includes error messages and retry count
- Enables manual investigation and replay

### 5. Observability Stack

**Prometheus:**
- Metrics collection and storage
- Custom metrics for events, latency, errors
- Alerting rules (configurable)

**Grafana:**
- Visualization dashboards
- Real-time monitoring
- Historical analysis

**Structured Logging:**
- JSON format for easy parsing
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR

## Data Flow

### Happy Path

1. Client sends event to API
2. API validates schema
3. API stores raw event in PostgreSQL
4. API publishes to Redis Streams
5. API returns 202 Accepted
6. Worker consumes from queue
7. Worker checks for duplicates
8. Worker validates business logic
9. Worker enriches event
10. Worker persists to processed_events
11. Worker acknowledges message
12. Metrics updated

### Failure Scenarios

**API Failure:**
- Client receives 500 error
- Client retries with backoff
- Raw event may or may not be stored

**Worker Crash:**
- Message not acknowledged
- Redis redelivers after timeout
- Idempotency prevents duplicate processing

**Database Failure:**
- Worker retries with exponential backoff
- After max retries, moves to DLQ
- Metrics track failure rate

**Invalid Event:**
- Validation fails
- Event moved to DLQ immediately
- Error logged with details

## Design Decisions

### 1. At-Least-Once Delivery

**Choice:** At-least-once delivery with idempotency

**Rationale:**
- Simpler than exactly-once
- Idempotency handles duplicates
- Better performance
- Easier to reason about

**Trade-offs:**
- Must implement idempotency checks
- Slightly higher database load
- Acceptable for most use cases

### 2. Redis Streams vs Kafka

**Choice:** Redis Streams

**Rationale:**
- Simpler setup and operations
- Sufficient for demo/small scale
- Consumer groups provide load balancing
- Easy to understand and debug

**Trade-offs:**
- Less throughput than Kafka
- Fewer ecosystem tools
- Not ideal for multi-datacenter
- Migration path exists if needed

### 3. PostgreSQL vs NoSQL

**Choice:** PostgreSQL

**Rationale:**
- ACID guarantees
- Rich querying capabilities
- JSON support for flexible schema
- Proven reliability
- Strong consistency

**Trade-offs:**
- Vertical scaling limits
- Write throughput ceiling
- More complex sharding
- Acceptable for most workloads

### 4. Async Processing

**Choice:** Python asyncio throughout

**Rationale:**
- Better resource utilization
- Higher concurrency
- Non-blocking I/O
- Scales horizontally

**Trade-offs:**
- More complex code
- Debugging challenges
- Learning curve
- Worth it for performance

## Scalability

### Horizontal Scaling

**Workers:**
- Add more worker containers
- Redis consumer groups distribute load
- No coordination needed
- Linear scaling up to queue throughput

**API:**
- Add more API containers
- Load balancer distributes requests
- Stateless design enables easy scaling

### Vertical Scaling

**Database:**
- Increase PostgreSQL resources
- Add read replicas for queries
- Connection pooling optimizes usage

**Redis:**
- Increase memory for larger queues
- Redis Cluster for sharding (if needed)

### Performance Targets

- **Throughput:** 1000+ events/second
- **Latency:** P95 < 100ms
- **Availability:** 99.9%
- **Data Durability:** 99.99%

## Reliability Patterns

### 1. Idempotency

Every event has a unique ID. Before processing, check if already processed.

```python
async def _is_duplicate(self, event_id: UUID) -> bool:
    result = await session.execute(
        select(ProcessedEventDB).where(ProcessedEventDB.event_id == event_id)
    )
    return result.scalar_one_or_none() is not None
```

### 2. Retry Logic

Exponential backoff for transient failures:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def _persist_event(self, event, enriched_data):
    # Database operation
```

### 3. Dead Letter Queue

Failed events moved to separate table for investigation:

```python
async def _move_to_dlq(self, event_data, error_message):
    failed_event = FailedEvent(
        event_id=event_data.get("event_id"),
        payload=event_data,
        error_message=error_message
    )
    session.add(failed_event)
```

### 4. Graceful Shutdown

Workers finish processing current messages before shutdown:

```python
async def shutdown(self):
    self.running = False
    await self.current_tasks
    await redis_client.disconnect()
```

## Monitoring and Observability

### Metrics

**Event Metrics:**
- `events_received_total` - Total events received by API
- `events_processed_total` - Total events successfully processed
- `events_failed_total` - Total events failed
- `events_duplicate_total` - Total duplicate events detected

**Performance Metrics:**
- `event_processing_duration` - Processing time histogram
- `queue_depth` - Current queue size
- `pending_messages` - Messages being processed

**System Metrics:**
- CPU, memory, disk usage
- Database connections
- Redis connections

### Logging

**Structured JSON logs:**
```json
{
  "timestamp": "2026-02-17T00:00:00Z",
  "level": "INFO",
  "message": "Event processed successfully",
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
  "processing_time_ms": 45.2,
  "worker_id": "worker-1"
}
```

### Health Checks

**API Health Check:**
- Database connectivity
- Redis connectivity
- Overall service status

**Worker Health:**
- Message consumption rate
- Error rate
- Processing latency

## Security Considerations

### Current Implementation

- No authentication (demo purposes)
- No rate limiting
- No input sanitization beyond schema validation

### Production Additions Needed

1. **Authentication/Authorization:**
   - API keys or OAuth2
   - Role-based access control

2. **Rate Limiting:**
   - Per-client limits
   - Global throughput limits

3. **Input Validation:**
   - Sanitize user inputs
   - Validate against injection attacks

4. **Network Security:**
   - TLS/SSL for all connections
   - Network isolation
   - Firewall rules

5. **Data Security:**
   - Encryption at rest
   - Encryption in transit
   - PII handling

## Future Enhancements

### Short Term
- Add authentication
- Implement rate limiting
- Create Grafana dashboards
- Add more event types

### Medium Term
- Migrate to Kafka
- Add distributed tracing (OpenTelemetry)
- Implement schema registry
- Add chaos engineering tests

### Long Term
- Multi-region deployment
- Event sourcing pattern
- CQRS implementation
- Kubernetes deployment

## Conclusion

EventFlow demonstrates production-grade distributed systems patterns:
- Fault tolerance through idempotency and retries
- Scalability through async processing and horizontal scaling
- Observability through metrics, logs, and health checks
- Reliability through at-least-once delivery and DLQ

The architecture balances simplicity with production readiness, making it suitable for both learning and real-world applications.
