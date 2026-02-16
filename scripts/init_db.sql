-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create raw_events table
CREATE TABLE IF NOT EXISTS raw_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID UNIQUE NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_events_event_id ON raw_events(event_id);
CREATE INDEX IF NOT EXISTS idx_raw_events_received_at ON raw_events(received_at);

-- Create processed_events table
CREATE TABLE IF NOT EXISTS processed_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    timestamp TIMESTAMP NOT NULL,
    properties JSONB,
    processed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    enriched_data JSONB,
    retry_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_processed_events_event_id ON processed_events(event_id);
CREATE INDEX IF NOT EXISTS idx_processed_events_event_type ON processed_events(event_type);
CREATE INDEX IF NOT EXISTS idx_processed_events_user_id ON processed_events(user_id);
CREATE INDEX IF NOT EXISTS idx_processed_events_status ON processed_events(status);
CREATE INDEX IF NOT EXISTS idx_processed_events_processed_at ON processed_events(processed_at);

-- Create failed_events table (Dead Letter Queue)
CREATE TABLE IF NOT EXISTS failed_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL,
    payload JSONB NOT NULL,
    error_message TEXT,
    failed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    retry_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_failed_events_event_id ON failed_events(event_id);
CREATE INDEX IF NOT EXISTS idx_failed_events_failed_at ON failed_events(failed_at);
