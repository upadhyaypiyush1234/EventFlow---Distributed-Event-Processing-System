#!/usr/bin/env python3
"""Load testing script"""

import argparse
import asyncio
import time
from datetime import datetime
from uuid import uuid4

import httpx


async def send_event(client: httpx.AsyncClient, api_url: str, event_num: int):
    """Send a single event"""
    event = {
        "event_id": str(uuid4()),
        "event_type": "purchase",
        "user_id": f"user_{event_num % 1000}",
        "timestamp": datetime.utcnow().isoformat(),
        "properties": {
            "amount": 99.99,
            "product_id": f"prod_{event_num}"
        }
    }
    
    start = time.time()
    try:
        response = await client.post(f"{api_url}/events", json=event)
        latency = (time.time() - start) * 1000
        return True, latency
    except Exception as e:
        latency = (time.time() - start) * 1000
        return False, latency


async def load_test(api_url: str, total_events: int, events_per_second: int):
    """Run load test"""
    print(f"Load Test Configuration:")
    print(f"  API URL: {api_url}")
    print(f"  Total Events: {total_events}")
    print(f"  Target Rate: {events_per_second} events/sec")
    print(f"  Duration: ~{total_events / events_per_second:.1f} seconds\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        success_count = 0
        failure_count = 0
        latencies = []
        
        start_time = time.time()
        
        for i in range(total_events):
            success, latency = await send_event(client, api_url, i)
            
            if success:
                success_count += 1
            else:
                failure_count += 1
            
            latencies.append(latency)
            
            # Progress update
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                avg_latency = sum(latencies[-100:]) / min(100, len(latencies))
                print(f"Progress: {i + 1}/{total_events} | "
                      f"Rate: {rate:.1f} req/s | "
                      f"Avg Latency: {avg_latency:.1f}ms | "
                      f"Success: {success_count} | "
                      f"Failed: {failure_count}")
            
            # Rate limiting
            if events_per_second > 0:
                await asyncio.sleep(1.0 / events_per_second)
        
        total_time = time.time() - start_time
        
        # Results
        print("\n" + "=" * 60)
        print("Load Test Results")
        print("=" * 60)
        print(f"Total Events:      {total_events}")
        print(f"Successful:        {success_count}")
        print(f"Failed:            {failure_count}")
        print(f"Success Rate:      {(success_count / total_events * 100):.2f}%")
        print(f"Total Time:        {total_time:.2f}s")
        print(f"Actual Rate:       {total_events / total_time:.2f} req/s")
        print(f"\nLatency Statistics:")
        print(f"  Min:             {min(latencies):.2f}ms")
        print(f"  Max:             {max(latencies):.2f}ms")
        print(f"  Avg:             {sum(latencies) / len(latencies):.2f}ms")
        print(f"  P50:             {sorted(latencies)[len(latencies) // 2]:.2f}ms")
        print(f"  P95:             {sorted(latencies)[int(len(latencies) * 0.95)]:.2f}ms")
        print(f"  P99:             {sorted(latencies)[int(len(latencies) * 0.99)]:.2f}ms")


def main():
    parser = argparse.ArgumentParser(description="Load test EventFlow")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument("--events", type=int, default=1000, help="Total events to send")
    parser.add_argument("--rate", type=int, default=100, help="Events per second")
    
    args = parser.parse_args()
    
    asyncio.run(load_test(args.api_url, args.events, args.rate))


if __name__ == "__main__":
    main()
