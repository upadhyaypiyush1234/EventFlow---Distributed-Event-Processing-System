from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration"""

    # Database
    database_url: str = "postgresql://eventflow:eventflow_pass@localhost:5432/eventflow"

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "events"
    redis_consumer_group: str = "workers"
    redis_block_ms: int = 5000

    # Worker
    worker_id: str = "worker-1"
    max_retries: int = 3
    retry_delay_seconds: int = 2
    batch_size: int = 10
    processing_timeout_seconds: int = 30

    # Logging
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Metrics
    metrics_port: int = 8001

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
