from pydantic import BaseModel, Field


class CheckRequest(BaseModel):
    api_key: str
    identifier: str
    cost: int = Field(default=1, ge=1)


class CheckResponse(BaseModel):
    allowed: bool
    remaining: int
    retry_after: float  # seconds
    reset_at: float     # unix seconds