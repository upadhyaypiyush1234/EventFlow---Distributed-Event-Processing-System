from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Counters
events_received_total = Counter(
    'events_received_total',
    'Total number of events received',
    ['event_type']
)

events_processed_total = Counter(
    'events_processed_total',
    'Total number of events processed successfully',
    ['event_type']
)

events_failed_total = Counter(
    'events_failed_total',
    'Total number of events that failed processing',
    ['event_type', 'error_type']
)

events_duplicate_total = Counter(
    'events_duplicate_total',
    'Total number of duplicate events detected',
    ['event_type']
)

# Gauges
queue_depth = Gauge(
    'queue_depth',
    'Current number of events in queue'
)

active_workers = Gauge(
    'active_workers',
    'Number of active worker processes'
)

# Histograms
event_processing_duration = Histogram(
    'event_processing_duration_seconds',
    'Time spent processing events',
    ['event_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

event_queue_wait_time = Histogram(
    'event_queue_wait_time_seconds',
    'Time events spend in queue before processing',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
)


def start_metrics_server(port: int = 8001):
    """Start Prometheus metrics server"""
    start_http_server(port)
