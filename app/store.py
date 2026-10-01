import redis.asyncio as redis
from app.config import REDIS_URL

# One client for the whole app; it manages a connection pool internally.
client = redis.from_url(REDIS_URL, decode_responses=True)