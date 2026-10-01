import asyncio

import pytest


@pytest.mark.parametrize("algorithm", ["fixed_window", "sliding_window", "token_bucket"])
async def test_exactly_limit_allowed_under_concurrency(make_key, client, algorithm):
    # Long window so the token bucket's refill is negligible during the test
    key = await make_key(algorithm=algorithm, limit=50, window_seconds=3600)

    async def one_request() -> bool:
        r = await client.post("/check", json={"api_key": key, "identifier": "u1"})
        assert r.status_code == 200, r.text
        return r.json()["allowed"]

    results = await asyncio.gather(*[one_request() for _ in range(200)])

    assert sum(results) == 50