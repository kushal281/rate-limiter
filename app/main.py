from fastapi import FastAPI, HTTPException
from redis.exceptions import RedisError

from app import limiter
from app.models import CheckRequest, CheckResponse, LimitConfig
from app.store import client, get_config, save_config, delete_config

app = FastAPI(title="Rate Limiter as a Service")

# The config lives in Redis, so if Redis is down we can't read fail_open from it.
fail_open_cache: dict[str, bool] = {}


@app.get("/health")
async def health():
    try:
        await client.ping()
        return {"redis": True}
    except Exception:
        return {"redis": False}


@app.post("/check", response_model=CheckResponse)
async def check(req: CheckRequest):
    try:
        cfg = await get_config(req.api_key)
        if cfg is None:
            raise HTTPException(status_code=404, detail="Unknown api_key")
        fail_open_cache[req.api_key] = cfg.fail_open
        return await limiter.check(req.api_key, req.identifier, req.cost, cfg)
    except RedisError:
        if fail_open_cache.get(req.api_key, False):
            # remaining=-1 means "unknown"
            return {"allowed": True, "remaining": -1, "retry_after": 0.0, "reset_at": 0.0}
        raise HTTPException(status_code=503, detail="Rate limiter store unavailable")


@app.put("/limits/{api_key}", response_model=LimitConfig)
async def put_limits(api_key: str, cfg: LimitConfig):
    return await save_config(api_key, cfg)


@app.get("/limits/{api_key}", response_model=LimitConfig)
async def get_limits(api_key: str):
    cfg = await get_config(api_key)
    if cfg is None:
        raise HTTPException(status_code=404, detail="Unknown api_key")
    return cfg


@app.delete("/limits/{api_key}", status_code=204)
async def delete_limits(api_key: str):
    if not await delete_config(api_key):
        raise HTTPException(status_code=404, detail="Unknown api_key")