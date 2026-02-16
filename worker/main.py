import asyncio
import json
import signal
from typing import Optional

from common.config import settings
from common.database import init_db
from common.logging_config import setup_logging
from common.metrics import active_workers, queue_depth, start_metrics_server
from common.redis_client import redis_client
from worker.processor import EventProcessor

logger = setup_logging("worker", settings.log_level)


class Worker:
    """Event processing worker"""

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.processor = EventProcessor(worker_id)
        self.running = False
        self.current_tasks = set()
        self.logger = logger

    async def start(self):
        """Start worker"""
        self.logger.info(f"Starting worker {self.worker_id}")

        # Initialize database
        await init_db()

        # Connect to Redis
        await redis_client.connect()

        # Start metrics server
        start_metrics_server(settings.metrics_port)

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        self.running = True
        active_workers.inc()

        try:
            await self._process_loop()
        finally:
            await self.shutdown()

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received shutdown signal: {signum}")
        self.running = False

    async def _process_loop(self):
        """Main processing loop"""
        self.logger.info(f"Worker {self.worker_id} ready to process events")

        while self.running:
            try:
                # Consume events from Redis stream
                messages = await redis_client.consume_events(
                    consumer_name=self.worker_id,
                    count=settings.batch_size,
                    block=settings.redis_block_ms,
                )

                if not messages:
                    continue

                # Update queue depth metric
                stream_length = await redis_client.get_stream_length()
                queue_depth.set(stream_length)

                # Process messages
                for message_id, message_data in messages:
                    if not self.running:
                        break

                    task = asyncio.create_task(
                        self._process_message(message_id, message_data)
                    )
                    self.current_tasks.add(task)
                    task.add_done_callback(self.current_tasks.discard)

                # Wait for batch to complete
                if self.current_tasks:
                    await asyncio.gather(*self.current_tasks, return_exceptions=True)
                    self.current_tasks.clear()

            except asyncio.CancelledError:
                self.logger.info("Worker cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in processing loop: {str(e)}", exc_info=True)
                await asyncio.sleep(5)  # Back off on error

    async def _process_message(self, message_id: str, message_data: dict):
        """Process a single message"""
        try:
            # Extract event data
            event_json = message_data.get("data")
            if not event_json:
                self.logger.error(f"No data in message {message_id}")
                await redis_client.acknowledge(message_id)
                return

            event_data = json.loads(event_json)

            # Process event with timeout
            success = await asyncio.wait_for(
                self.processor.process_event(event_data, message_id),
                timeout=settings.processing_timeout_seconds,
            )

            # Acknowledge message
            if success:
                await redis_client.acknowledge(message_id)
            else:
                # Let message timeout and be reprocessed
                self.logger.warning(
                    f"Event processing failed, message will be retried",
                    extra={"message_id": message_id},
                )

        except asyncio.TimeoutError:
            self.logger.error(
                f"Processing timeout for message {message_id}",
                extra={"message_id": message_id},
            )
        except Exception as e:
            self.logger.error(
                f"Error processing message {message_id}: {str(e)}",
                extra={"message_id": message_id},
                exc_info=True,
            )

    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info(f"Shutting down worker {self.worker_id}")

        self.running = False

        # Wait for current tasks to complete
        if self.current_tasks:
            self.logger.info(f"Waiting for {len(self.current_tasks)} tasks to complete")
            await asyncio.gather(*self.current_tasks, return_exceptions=True)

        # Disconnect from Redis
        await redis_client.disconnect()

        active_workers.dec()
        self.logger.info(f"Worker {self.worker_id} shutdown complete")


async def main():
    """Main entry point"""
    worker = Worker(settings.worker_id)
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
