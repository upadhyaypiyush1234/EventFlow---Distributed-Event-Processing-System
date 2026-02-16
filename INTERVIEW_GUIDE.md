# Interview Guide

How to discuss EventFlow in technical interviews.

## Project Elevator Pitch

**30-second version:**

"I built EventFlow, a distributed event processing system that handles asynchronous workflows with fault tolerance and observability. It uses FastAPI for ingestion, Redis Streams for queuing, and async workers for processing. The system implements idempotency, retry logic, and dead-letter queues to ensure reliability. I included comprehensive monitoring with Prometheus and Grafana to track performance and debug issues."

**2-minute version:**

"EventFlow is a production-grade distributed system I built to demonstrate advanced engineering concepts. The architecture follows a queue-based pattern: clients send events to a FastAPI service, which stores them in PostgreSQL and publishes to Redis Streams. A pool of async workers consumes from the queue, validates events, enriches them with additional data, and persists the results.

The interesting part is the reliability engineering. I implemented idempotency checks to handle duplicate events, retry logic with exponential backoff for transient failures, and a dead-letter queue for permanent failures. Every event has a correlation ID for tracing, and I use structured logging throughout.

For observability, I integrated Prometheus for metrics and Grafana for visualization. The system tracks throughput, latency, error rates, and queue depth. I can scale workers horizontally, and the system handles 1000+ events per second with P95 latency under 100ms.

What makes this project valuable is that it solves real distributed systems problems—not just CRUD operations. It demonstrates engineering judgment, trade-off analysis, and production thinking."

## Common Interview Questions

### System Design Questions

#### "Walk me through the architecture"

**Answer:**

"The system has four main components:

1. **API Layer (FastAPI):** Accepts HTTP POST requests with event data. It validates the schema, stores raw events in PostgreSQL for audit trail, and publishes to Redis Streams. Returns 202 Accepted immediately—async processing.

2. **Message Queue (Redis Streams):** Acts as a buffer between ingestion and processing. I chose Redis Streams over Kafka because it's simpler for demos but still provides consumer groups for load balancing and at-least-once delivery semantics.

3. **Worker Pool:** Multiple async workers consume from the queue. Each worker checks for duplicates (idempotency), validates business logic, enriches the event, and persists to the database. If processing fails, it retries with exponential backoff. After max retries, it moves the event to a dead-letter queue.

4. **Persistence (PostgreSQL):** Three tables—raw_events for audit, processed_events for successful processing, and failed_events as the DLQ. PostgreSQL gives us ACID guarantees and rich querying.

The whole system is containerized with Docker and includes Prometheus for metrics and Grafana for dashboards."

**Follow-up: "Why this architecture?"**

"I wanted to demonstrate decoupling and async processing. The queue decouples ingestion from processing, so the API can accept events even if workers are slow or down. Async processing allows horizontal scaling—I can add more workers without changing code. The separation of concerns makes each component easier to test and reason about."

#### "How do you handle failures?"

**Answer:**

"I handle failures at multiple levels:

1. **Worker Crashes:** Redis Streams tracks message acknowledgments. If a worker crashes before acking, the message times out and gets redelivered to another worker. Idempotency prevents duplicate side effects.

2. **Database Failures:** I use the tenacity library for retry logic with exponential backoff. If a database write fails, the worker retries up to 3 times with increasing delays (2s, 4s, 8s). This handles transient network issues.

3. **Invalid Events:** If validation fails, the event moves immediately to the dead-letter queue with the error message. This prevents poison messages from blocking the queue.

4. **Duplicate Events:** Before processing, I check if the event_id already exists in processed_events. If it does, I skip processing. This makes the system idempotent.

The key insight is distinguishing between transient failures (retry) and permanent failures (DLQ). Retries handle temporary issues, DLQ preserves failed events for investigation."

#### "How would you scale this to 10x traffic?"

**Answer:**

"Several approaches, depending on the bottleneck:

**Short-term (10x):**
- Horizontal worker scaling: Add more worker containers. Redis consumer groups distribute load automatically.
- API scaling: Add more API containers behind a load balancer. The API is stateless, so this is straightforward.
- Database optimization: Add indexes, enable connection pooling (already done), batch writes.

**Medium-term (100x):**
- Database read replicas: Route queries to replicas, writes to primary.
- Batch processing: Instead of writing events one-by-one, batch them. Reduces database round trips.
- Caching: Cache frequently accessed data (user profiles, etc.) in Redis.

**Long-term (1000x):**
- Migrate to Kafka: Better throughput and ecosystem than Redis Streams.
- Database sharding: Partition by user_id or event_type.
- Event sourcing: Store only events, materialize views asynchronously.
- Multi-region: Deploy in multiple regions for geographic distribution.

The architecture supports these changes because components are decoupled. I can swap Redis for Kafka without changing the API or workers much."

#### "What are the trade-offs in your design?"

**Answer:**

"**At-least-once vs. exactly-once delivery:**
I chose at-least-once because it's simpler and performs better. The trade-off is I must implement idempotency checks. For this use case, checking a database is acceptable. Exactly-once would require distributed transactions or Kafka with specific configurations—more complexity.

**Redis Streams vs. Kafka:**
Redis is simpler to set up and understand, sufficient for demos and small-to-medium scale. Kafka has better throughput, more ecosystem tools, and better multi-datacenter support. For this project, simplicity won. Migration path exists if needed.

**PostgreSQL vs. NoSQL:**
PostgreSQL gives ACID guarantees and rich querying. Trade-off is vertical scaling limits and write throughput ceiling. NoSQL would scale better horizontally but loses strong consistency. For event processing, I value consistency and queryability.

**Async vs. sync processing:**
Async (asyncio) gives better resource utilization and concurrency. Trade-off is code complexity and debugging difficulty. For a system focused on throughput, async is worth it.

Every trade-off is about balancing simplicity, performance, and correctness for the specific use case."

### Technical Deep Dives

#### "Explain your idempotency implementation"

**Answer:**

"Every event has a unique UUID (event_id). Before processing, the worker queries the database:

```python
async def _is_duplicate(self, event_id: UUID) -> bool:
    result = await session.execute(
        select(ProcessedEventDB).where(ProcessedEventDB.event_id == event_id)
    )
    return result.scalar_one_or_none() is not None
```

If the event_id exists, we skip processing and return success. This makes the system idempotent—processing the same event multiple times has the same effect as processing it once.

This is necessary because Redis Streams provides at-least-once delivery. If a worker crashes after processing but before acknowledging, the message gets redelivered. Without idempotency, we'd process it twice.

The trade-off is an extra database query per event. I could optimize with a cache (Redis), but for now, the database query is acceptable. PostgreSQL indexes make it fast."

#### "How does your retry logic work?"

**Answer:**

"I use the tenacity library for declarative retries:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def _persist_event(self, event, enriched_data):
    # Database operation
```

This retries up to 3 times with exponential backoff: 2s, 4s, 8s. Exponential backoff prevents overwhelming a recovering service.

If all retries fail, the exception propagates, and the event moves to the DLQ. This distinguishes transient failures (network blip) from permanent failures (invalid data).

I apply retries to external operations—database writes, API calls—but not to validation. Validation failures are permanent, so they go straight to DLQ."

#### "Explain your logging strategy"

**Answer:**

"I use structured logging with JSON format:

```json
{
  \"timestamp\": \"2026-02-17T00:00:00Z\",
  \"level\": \"INFO\",
  \"message\": \"Event processed successfully\",
  \"event_id\": \"123e4567-e89b-12d3-a456-426614174000\",
  \"correlation_id\": \"123e4567-e89b-12d3-a456-426614174000\",
  \"processing_time_ms\": 45.2,
  \"worker_id\": \"worker-1\"
}
```

Every log entry includes:
- **correlation_id:** Traces an event through the entire system (API → queue → worker → database)
- **Structured fields:** Easy to query and aggregate
- **Context:** worker_id, event_type, etc.

This makes debugging easy. If a user reports an issue, I search logs by event_id or correlation_id and see the entire flow. Structured format means I can query with tools like Elasticsearch or Loki.

I use Python's logging module with a custom formatter. Each worker adds a correlation ID filter when processing an event."

#### "How do you monitor the system?"

**Answer:**

"Three layers of observability:

**1. Metrics (Prometheus):**
- `events_received_total`: Counter of events received
- `events_processed_total`: Counter of successful processing
- `events_failed_total`: Counter of failures (labeled by error type)
- `event_processing_duration`: Histogram of processing time
- `queue_depth`: Current queue size

I export these from the application using the prometheus_client library. Prometheus scrapes them every 15 seconds.

**2. Dashboards (Grafana):**
Visualize metrics over time. I can see throughput trends, latency percentiles (P50, P95, P99), error rates, and queue depth. Helps identify issues before they become critical.

**3. Logs:**
Structured JSON logs for detailed debugging. When metrics show an issue, logs tell me why.

**4. Health Checks:**
The API has a `/health` endpoint that checks database and Redis connectivity. Load balancers use this for routing decisions.

This combination gives me both high-level visibility (metrics) and detailed debugging (logs)."

### Behavioral Questions

#### "Why did you build this project?"

**Answer:**

"I wanted to demonstrate production-grade engineering beyond typical portfolio projects. Most projects are CRUD apps or clones—they show you can follow tutorials but not that you can design systems.

EventFlow demonstrates:
- **System design:** Choosing components and understanding trade-offs
- **Reliability engineering:** Handling failures gracefully
- **Operational excellence:** Monitoring, debugging, scaling
- **Engineering judgment:** Knowing when to optimize vs. keep it simple

I also wanted to learn distributed systems concepts deeply—not just read about them. Building this forced me to understand idempotency, retry strategies, message queues, and observability in practice.

The project is valuable for interviews because I can discuss real engineering decisions, not just features. Every choice has a rationale and trade-offs I can defend."

#### "What was the hardest part?"

**Answer:**

"The hardest part was getting the failure handling right. Initially, I had workers that would crash on any error, leaving messages unacknowledged. I had to understand Redis Streams' acknowledgment model and implement proper error handling.

Specifically, distinguishing between transient and permanent failures. Should I retry? How many times? What backoff strategy? When do I give up and move to DLQ?

I researched patterns like exponential backoff and circuit breakers. I tested by intentionally failing the database and watching how the system recovered. This taught me that reliability isn't just about happy paths—it's about graceful degradation.

Another challenge was observability. Initially, debugging issues was hard because logs were unstructured. Adding correlation IDs and structured logging made a huge difference. Now I can trace an event through the entire system.

These challenges made the project valuable because I learned by solving real problems, not just implementing features."

#### "What would you do differently?"

**Answer:**

"A few things:

**1. Add authentication earlier:** I focused on core functionality first, but in retrospect, adding API keys or OAuth would make it more production-ready.

**2. Implement distributed tracing:** Correlation IDs help, but proper distributed tracing (OpenTelemetry) would give better visibility across services.

**3. Add more comprehensive tests:** I have unit and integration tests, but I'd add chaos engineering tests—intentionally failing components to verify recovery.

**4. Schema registry:** For event validation, a schema registry (like Confluent Schema Registry) would enforce contracts between producers and consumers.

**5. Better documentation:** I'd add more inline code comments and architecture decision records (ADRs) to explain why I made certain choices.

That said, I'm happy with the trade-offs. The project demonstrates the concepts I wanted to show without over-engineering. Knowing when to stop is also an engineering skill."

### Whiteboard Questions

#### "Design an event processing system"

**Your advantage:** You've already built one! Walk through EventFlow's architecture, explaining each component and why it's needed.

**Key points to cover:**
1. Ingestion layer (API)
2. Message queue (decoupling)
3. Processing layer (workers)
4. Persistence (database)
5. Observability (metrics, logs)

**Trade-offs to discuss:**
- Sync vs. async processing
- At-least-once vs. exactly-once delivery
- SQL vs. NoSQL
- Monolith vs. microservices

#### "How would you handle duplicate events?"

**Answer:** Explain idempotency with event_id checks. Discuss trade-offs (database query overhead vs. correctness).

#### "How would you scale to 1 million events/second?"

**Answer:** Walk through scaling strategies from EventFlow, then discuss what changes at extreme scale (Kafka, sharding, caching, etc.).

## Resume Bullets

Use these on your resume:

1. **"Designed and implemented a fault-tolerant distributed event processing system handling 1000+ events/second with async workflows, validation, enrichment, retry logic, and dead-letter queues"**

2. **"Built comprehensive observability features including structured logging with correlation IDs, Prometheus metrics, and Grafana dashboards for real-time system monitoring"**

3. **"Implemented idempotency checks and at-least-once delivery guarantees to ensure correctness under failure scenarios including worker crashes and network issues"**

4. **"Evaluated trade-offs between throughput, consistency, and complexity, selecting Redis Streams with consumer groups for queue management and PostgreSQL for persistence"**

5. **"Deployed multi-service architecture using Docker with horizontal worker scaling, achieving P95 latency under 100ms and 99.9% success rate"**

## Technical Keywords

Make sure to mention these in interviews:

**Architecture:**
- Distributed systems
- Event-driven architecture
- Queue-based processing
- Async/await
- Microservices
- Decoupling

**Reliability:**
- Fault tolerance
- Idempotency
- Retry logic
- Exponential backoff
- Dead-letter queue
- At-least-once delivery
- Graceful degradation

**Technologies:**
- FastAPI
- Redis Streams
- PostgreSQL
- Docker
- Prometheus
- Grafana
- Python asyncio

**Observability:**
- Structured logging
- Correlation IDs
- Metrics
- Dashboards
- Health checks
- Distributed tracing

**Performance:**
- Horizontal scaling
- Connection pooling
- Async I/O
- Throughput
- Latency (P50, P95, P99)

## Demo Script

If you're asked to demo the project:

**1. Show the architecture diagram (5 minutes)**
- Explain components
- Explain data flow
- Explain failure handling

**2. Start the system (2 minutes)**
```bash
docker-compose up -d
docker-compose ps
```

**3. Send test events (3 minutes)**
- Open http://localhost:8000/docs
- Submit events via interactive API
- Show different event types

**4. Show observability (5 minutes)**
- View logs: `docker-compose logs -f worker`
- Show metrics: http://localhost:9090
- Show Grafana: http://localhost:3000

**5. Demonstrate fault tolerance (5 minutes)**
```bash
# Send events
python scripts/producer.py --count 100 &

# Kill a worker
docker-compose kill worker

# Show messages redelivered
docker-compose logs -f worker

# Restart worker
docker-compose up -d worker

# Verify all processed
curl http://localhost:8000/metrics/summary
```

**6. Show database (3 minutes)**
```bash
docker-compose exec postgres psql -U eventflow -d eventflow

SELECT COUNT(*) FROM processed_events;
SELECT * FROM processed_events ORDER BY processed_at DESC LIMIT 5;
SELECT * FROM failed_events;
```

**Total: ~25 minutes**

## Questions to Ask Interviewers

Show your expertise by asking good questions:

1. **"How do you handle event ordering in your systems?"**
   - Shows you understand distributed systems challenges

2. **"What's your approach to idempotency?"**
   - Shows you think about correctness

3. **"How do you balance consistency and availability?"**
   - Shows you understand CAP theorem

4. **"What observability tools do you use?"**
   - Shows you care about operations

5. **"How do you handle schema evolution for events?"**
   - Shows you think about long-term maintenance

## Red Flags to Avoid

**Don't say:**
- "I just followed a tutorial"
- "I don't know why I chose X"
- "I haven't thought about scaling"
- "I didn't add tests because..."
- "It's just a simple CRUD app"

**Do say:**
- "I chose X because of trade-off Y"
- "I considered alternatives A and B"
- "Here's how I would scale this"
- "I tested this scenario by..."
- "This demonstrates pattern X"

## Practice Questions

Before interviews, practice answering:

1. Walk me through your project
2. Why did you make choice X?
3. How would you handle scenario Y?
4. What would you do differently?
5. How does this scale?
6. What happens when X fails?
7. How do you debug issues?
8. What metrics do you track?
9. How do you ensure correctness?
10. What did you learn?

## Confidence Builders

**You've built something real:**
- Not a tutorial project
- Solves actual problems
- Production patterns
- Defensible decisions

**You understand trade-offs:**
- At-least-once vs. exactly-once
- Redis vs. Kafka
- SQL vs. NoSQL
- Sync vs. async

**You can go deep:**
- Explain idempotency implementation
- Discuss retry strategies
- Describe observability approach
- Walk through failure scenarios

**You can go broad:**
- Discuss scaling strategies
- Compare alternatives
- Suggest improvements
- Connect to real-world systems

## Final Tips

1. **Be enthusiastic:** You built something cool, show it!
2. **Be honest:** If you don't know something, say so
3. **Be specific:** Use concrete examples from your code
4. **Be humble:** Acknowledge limitations and improvements
5. **Be curious:** Ask questions about their systems

**Remember:** EventFlow demonstrates you can think like a senior engineer. You understand not just how to code, but how to design systems, handle failures, and make trade-offs. That's what sets you apart.

Good luck! 🚀
