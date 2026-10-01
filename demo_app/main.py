import math
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

LIMITER_URL = os.getenv("LIMITER_URL", "http://localhost:8000")

app = FastAPI(title="Demo API")
http = httpx.AsyncClient(base_url=LIMITER_URL, timeout=1.0)


def rate_headers(result: dict) -> dict:
    if result["remaining"] < 0:  # fail-open: quota unknown, send no headers
        return {}
    return {
        "X-RateLimit-Limit": str(result["limit"]),
        "X-RateLimit-Remaining": str(result["remaining"]),
    }


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return JSONResponse({"detail": "Missing X-API-Key"}, status_code=401)

    try:
        resp = await http.post(
            "/check", json={"api_key": api_key, "identifier": request.client.host}
        )
    except httpx.HTTPError:
        return JSONResponse({"detail": "Rate limiter unreachable"}, status_code=503)

    if resp.status_code == 404:
        return JSONResponse({"detail": "Unknown API key"}, status_code=401)
    if resp.status_code != 200:
        return JSONResponse({"detail": "Rate limiter error"}, status_code=503)

    result = resp.json()
    headers = rate_headers(result)

    if not result["allowed"]:
        headers["Retry-After"] = str(math.ceil(result["retry_after"]))
        return JSONResponse(
            {"detail": "Rate limit exceeded"}, status_code=429, headers=headers
        )

    response = await call_next(request)
    response.headers.update(headers)
    return response


@app.get("/hello")
async def hello():
    return {"message": "hello"}