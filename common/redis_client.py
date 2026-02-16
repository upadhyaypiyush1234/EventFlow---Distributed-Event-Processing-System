import json
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from common.config import settings


class RedisClient:
    """Redis client for stream operations"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.stream_name = settings.redis_stream_name
        self.consumer_group = settings.redis_consumer_group

    async def connect(self):
        """Connect to Redis"""
        self.redis = await redis.from_url(
            settings.redis_url, encoding="utf-8", decode_responses=True
        )

        # Create consumer group if it doesn't exist
        try:
            await self.redis.xgroup_create(
                name=self.stream_name,
                groupname=self.consumer_group,
                id="0",
                mkstream=True,
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()

    async def publish_event(self, event_data: Dict[str, Any]) -> str:
        """Publish event to stream"""
        message_id = await self.redis.xadd(
            self.stream_name, {"data": json.dumps(event_data)}
        )
        return message_id

    async def consume_events(
        self, consumer_name: str, count: int = 10, block: int = 5000
    ) -> List[tuple]:
        """Consume events from stream"""
        messages = await self.redis.xreadgroup(
            groupname=self.consumer_group,
            consumername=consumer_name,
            streams={self.stream_name: ">"},
            count=count,
            block=block,
        )

        if not messages:
            return []

        # Extract messages from response
        stream_messages = messages[0][1]  # [(stream_name, [(id, data)])]
        return stream_messages

    async def acknowledge(self, message_id: str):
        """Acknowledge message processing"""
        await self.redis.xack(self.stream_name, self.consumer_group, message_id)

    async def get_pending_count(self) -> int:
        """Get count of pending messages"""
        pending_info = await self.redis.xpending(self.stream_name, self.consumer_group)
        return pending_info["pending"]

    async def get_stream_length(self) -> int:
        """Get stream length"""
        return await self.redis.xlen(self.stream_name)

    async def check_health(self) -> bool:
        """Check Redis connectivity"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False


# Global instance
redis_client = RedisClient()
