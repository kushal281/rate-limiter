import redis.asyncio as redis
from app.config import REDIS_URL
from app.models import LimitConfig

pool = redis.BlockingConnectionPool.from_url(
    REDIS_URL,
    max_connections=100,
    timeout=5,
    decode_responses=True,
)
client = redis.Redis(connection_pool=pool)

def _cfg_key(api_key: str) -> str:
    return f"cfg:{api_key}"


async def save_config(api_key: str, cfg: LimitConfig) -> LimitConfig:
    cfg = cfg.model_copy(update={"burst": cfg.burst or cfg.limit})
    data = cfg.model_dump()
    data["fail_open"] = int(data["fail_open"])  # Redis hashes store strings/numbers
    await client.hset(_cfg_key(api_key), mapping=data)
    return cfg


async def get_config(api_key: str) -> LimitConfig | None:
    data = await client.hgetall(_cfg_key(api_key))
    return LimitConfig(**data) if data else None  # pydantic converts "5" -> 5


async def delete_config(api_key: str) -> bool:
    return await client.delete(_cfg_key(api_key)) == 1