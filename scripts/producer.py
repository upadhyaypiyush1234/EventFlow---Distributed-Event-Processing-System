#!/usr/bin/env python3
"""Event producer for testing"""

import argparse
import asyncio
import random
from datetime import datetime
from uuid import uuid4

import httpx

EVENT_TYPES = ["purchase", "user_signup", "page_view", "custom"]

SAMPLE_EVENTS = {
    "purchase": {
        "amount": lambda: random.uniform(10, 5000),
        "product_id": lambda: f"prod_{random.randint(1000, 9999)}",
        "currency": lambda: random.choice(["USD", "EUR", "GBP"])
    },
    "user_signup": {
        "email": lambda: f"user{random.randint(1000, 9999)}@example.com",
        "source": lambda: random.choice(["web", "mobile", "api"])
    },
    "page_view": {
        "url": lambda: f"/page/{random.randint(1, 100)}",
        "referrer": lambda: random.choice(["google", "direct", "social"])
    },
    "custom": {
        "action": lambda: random.choice(["click", "scroll", "hover"]),
        "value": lambda: random.randint(1, 100)
    }
}


async def generate_event(event_type: str = None):
    """Generate a random event"""
    if not event_type:
        event_type = random.choice(EVENT_TYPES)
    
    properties = {}
    if event_type in SAMPLE_EVENTS:
        for key, value_fn in SAMPLE_EVENTS[event_type].items():
            properties[key] = value_fn()
    
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "user_id": f"user_{random.randint(1, 1000)}",
        "timestamp": datetime.utcnow().isoformat(),
        "properties": properties
    }


async def send_event(client: httpx.AsyncClient, api_url: str, event: dict):
    """Send event to API"""
    try:
        response = await client.post(f"{api_url}/events", json=event)
        response.raise_for_status()
        return True, event["event_id"]
    except Exception as e:
        return False, str(e)


async def produce_events(api_url: str, count: int, rate: int, event_type: str = None):
    """Produce events at specified rate"""
    print(f"Producing {count} events at {rate} events/sec to {api_url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        success_count = 0
        failure_count = 0
        
        for i in range(count):
            event = await generate_event(event_type)
            success, result = await send_event(client, api_url, event)
            
            if success:
                success_count += 1
                if (i + 1) % 10 == 0:
                    print(f"Sent {i + 1}/{count} events (Success: {success_count}, Failed: {failure_count})")
            else:
                failure_count += 1
                print(f"Failed to send event: {result}")
            
            # Rate limiting
            if rate > 0:
                await asyncio.sleep(1.0 / rate)
        
        print(f"\nCompleted: {success_count} successful, {failure_count} failed")


def main():
    parser = argparse.ArgumentParser(description="Event producer for testing")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument("--count", type=int, default=100, help="Number of events to produce")
    parser.add_argument("--rate", type=int, default=10, help="Events per second (0 = unlimited)")
    parser.add_argument("--type", choices=EVENT_TYPES, help="Event type (random if not specified)")
    
    args = parser.parse_args()
    
    asyncio.run(produce_events(args.api_url, args.count, args.rate, args.type))


if __name__ == "__main__":
    main()
