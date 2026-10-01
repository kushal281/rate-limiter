from pydantic import BaseModel, Field
from typing import Literal


class CheckRequest(BaseModel):
    api_key: str
    identifier: str
    cost: int = Field(default=1, ge=1)


class CheckResponse(BaseModel):
    allowed: bool
    limit: int
    remaining: int
    retry_after: float  # seconds
    reset_at: float     # unix seconds
    

class LimitConfig(BaseModel):
    algorithm: Literal["fixed_window", "sliding_window", "token_bucket"]
    limit: int = Field(ge=1)
    window_seconds: int = Field(ge=1)
    burst: int | None = Field(default=None, ge=1)  # token bucket capacity; defaults to limit
    fail_open: bool = False