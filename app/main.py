from fastapi import FastAPI
from app.store import client

app = FastAPI(title="Rate Limiter as a Service")


@app.get("/health")
async def health():
    try:
        await client.ping()
        return {"redis": True}
    except Exception:
        return {"redis": False}