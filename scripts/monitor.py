#!/usr/bin/env python3
"""Monitor system metrics"""

import argparse
import asyncio
import time

import httpx


async def get_metrics(api_url: str):
    """Get current metrics"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{api_url}/metrics/summary")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}


async def monitor_loop(api_url: str, interval: int):
    """Monitor metrics in a loop"""
    print(f"Monitoring {api_url} (refresh every {interval}s)")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            metrics = await get_metrics(api_url)

            # Clear screen (works on Unix and Windows)
            print("\033[2J\033[H", end="")

            print("=" * 60)
            print(f"EventFlow Metrics - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            if "error" in metrics:
                print(f"\nError: {metrics['error']}")
            else:
                print(f"\nQueue Length:      {metrics.get('queue_length', 0)}")
                print(f"Pending Messages:  {metrics.get('pending_messages', 0)}")
                print(f"Timestamp:         {metrics.get('timestamp', 'N/A')}")

            print("\n" + "=" * 60)
            print(f"Next update in {interval} seconds...")

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")


def main():
    parser = argparse.ArgumentParser(description="Monitor EventFlow metrics")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API URL")
    parser.add_argument(
        "--interval", type=int, default=5, help="Refresh interval in seconds"
    )

    args = parser.parse_args()

    asyncio.run(monitor_loop(args.api_url, args.interval))


if __name__ == "__main__":
    main()
