from fastapi import FastAPI
from app.store import client
from app.models import CheckRequest, CheckResponse
from app.limiter import check_fixed_window
from app.limiter import check_fixed_window, check_sliding_window, check_token_bucket

app = FastAPI(title="Rate Limiter as a Service")
ALGOS = {
    "fixed": check_fixed_window,
    "sliding": check_sliding_window,
    "token": check_token_bucket,
}

@app.get("/health")
async def health():
    try:
        await client.ping()
        return {"redis": True}
    except Exception:
        return {"redis": False}


@app.post("/check", response_model=CheckResponse)
async def check(req: CheckRequest, algo: str = "fixed"):
    return await ALGOS[algo](req.api_key, req.identifier, req.cost)