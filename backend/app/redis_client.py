"""
Redis Client - Cache and Session Management
"""
import redis.asyncio as aioredis
import json
from typing import Optional, Any

from app.config import settings


class RedisClient:
    """Async Redis client wrapper"""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Initialize Redis connection"""
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )

    @property
    def client(self) -> aioredis.Redis:
        if self._redis is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def set(self, key: str, value: Any, expire: int = 3600):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.client.set(key, value, ex=expire)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def get_json(self, key: str) -> Optional[dict]:
        data = await self.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_json(self, key: str, value: dict, expire: int = 3600):
        await self.set(key, json.dumps(value), expire)

    async def disconnect(self):
        if self._redis:
            await self._redis.close()
            self._redis = None


redis_client = RedisClient()
