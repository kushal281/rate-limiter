import os
import uuid

import httpx
import pytest_asyncio

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@pytest_asyncio.fixture
async def client():
    limits = httpx.Limits(max_connections=200)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10, limits=limits) as c:
        yield c


@pytest_asyncio.fixture
async def make_key(client):
    """Create a config under a fresh random api_key; delete it afterwards."""
    created = []

    async def _make(**cfg):
        api_key = f"test-{uuid.uuid4().hex[:8]}"
        r = await client.put(f"/limits/{api_key}", json=cfg)
        assert r.status_code == 200, r.text
        created.append(api_key)
        return api_key

    yield _make
    for key in created:
        await client.delete(f"/limits/{key}")


@pytest_asyncio.fixture
async def check(client):
    async def _check(api_key, identifier="u1", cost=1):
        r = await client.post(
            "/check", json={"api_key": api_key, "identifier": identifier, "cost": cost}
        )
        assert r.status_code == 200, r.text
        return r.json()

    return _check