# Product Overview

EventFlow is a production-grade distributed event processing system that demonstrates real-world patterns for building reliable, scalable microservices.

## Core Functionality

The system processes events through a complete pipeline:
- Event ingestion via REST API
- Reliable queuing with Redis Streams
- Asynchronous worker-based processing
- Persistent storage in PostgreSQL
- Automatic failure handling and retries
- Real-time monitoring and observability

## Key Design Principles

- **Fault Tolerance**: At-least-once delivery with idempotency checks
- **Scalability**: Horizontal scaling via worker pool and async I/O
- **Observability**: Structured logging, Prometheus metrics, correlation IDs
- **Reliability**: Retry logic, dead letter queue, graceful degradation

## Use Cases

This architecture pattern applies to:
- Analytics pipelines (user behavior tracking)
- Notification systems (async email/SMS)
- Data synchronization across systems
- Audit logging for compliance
- Event sourcing architectures
