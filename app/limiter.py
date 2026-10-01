import uuid
from pathlib import Path
from app.store import client

SCRIPTS = Path(__file__).parent / "scripts"

# register_script gives a callable that runs the script via EVALSHA
fixed_window_script = client.register_script(
    (SCRIPTS / "fixed_window.lua").read_text()
)
sliding_window_script = client.register_script(
    (SCRIPTS / "sliding_window.lua").read_text()
)


# Temporary hardcoded limits; replaced by per-key config in Step 5
LIMIT = 5
WINDOW_SECONDS = 10


def _result(raw) -> dict:
    allowed, remaining, retry_ms, reset_ms = raw
    return {
        "allowed": bool(allowed),
        "remaining": remaining,
        "retry_after": retry_ms / 1000,
        "reset_at": reset_ms / 1000,
    }


async def check_fixed_window(api_key: str, identifier: str, cost: int) -> dict:
    key = f"rl:fw:{api_key}:{identifier}"
    raw = await fixed_window_script(keys=[key], args=[LIMIT, WINDOW_SECONDS, cost])
    return _result(raw)


async def check_sliding_window(api_key: str, identifier: str, cost: int) -> dict:
    key = f"rl:sw:{api_key}:{identifier}"
    raw = await sliding_window_script(
        keys=[key], args=[LIMIT, WINDOW_SECONDS, cost, uuid.uuid4().hex]
    )
    return _result(raw)