import uuid
from pathlib import Path
from app.store import client
from app.models import LimitConfig

SCRIPTS = Path(__file__).parent / "scripts"

# register_script gives a callable that runs the script via EVALSHA
fixed_window_script = client.register_script(
    (SCRIPTS / "fixed_window.lua").read_text()
)

sliding_window_script = client.register_script(
    (SCRIPTS / "sliding_window.lua").read_text()
)

token_bucket_script = client.register_script(
    (SCRIPTS / "token_bucket.lua").read_text()
)


def _result(raw) -> dict:
    allowed, remaining, retry_ms, reset_ms = raw
    return {
        "allowed": bool(allowed),
        "remaining": remaining,
        "retry_after": retry_ms / 1000,
        "reset_at": reset_ms / 1000,
    }


async def check_fixed_window(api_key, identifier, cost, cfg: LimitConfig) -> dict:
    key = f"rl:fw:{api_key}:{identifier}"
    raw = await fixed_window_script(
        keys=[key], args=[cfg.limit, cfg.window_seconds, cost]
    )
    return _result(raw)


async def check_sliding_window(api_key, identifier, cost, cfg: LimitConfig) -> dict:
    key = f"rl:sw:{api_key}:{identifier}"
    raw = await sliding_window_script(
        keys=[key], args=[cfg.limit, cfg.window_seconds, cost, uuid.uuid4().hex]
    )
    return _result(raw)


async def check_token_bucket(api_key, identifier, cost, cfg: LimitConfig) -> dict:
    key = f"rl:tb:{api_key}:{identifier}"
    refill_rate = cfg.limit / cfg.window_seconds  # tokens per second
    raw = await token_bucket_script(keys=[key], args=[cfg.burst, refill_rate, cost])
    return _result(raw)


ALGOS = {
    "fixed_window": check_fixed_window,
    "sliding_window": check_sliding_window,
    "token_bucket": check_token_bucket,
}


async def check(api_key, identifier, cost, cfg: LimitConfig) -> dict:
    return await ALGOS[cfg.algorithm](api_key, identifier, cost, cfg)