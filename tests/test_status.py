import pytest

CONFIGS = {
    "fixed_window": dict(algorithm="fixed_window", limit=3, window_seconds=60),
    "sliding_window": dict(algorithm="sliding_window", limit=3, window_seconds=60),
    "token_bucket": dict(algorithm="token_bucket", limit=3, window_seconds=60, burst=3),
}


async def get_status(client, key, identifier="u1"):
    r = await client.get(f"/status/{key}/{identifier}")
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("name", CONFIGS)
async def test_status_does_not_consume_quota(name, client, make_key, check):
    key = await make_key(**CONFIGS[name])
    for _ in range(5):  # peek many times...
        assert (await get_status(client, key))["remaining"] == 3
    # ...and all 3 real requests are still available
    results = [await check(key) for _ in range(4)]
    assert [r["allowed"] for r in results] == [True, True, True, False]


@pytest.mark.parametrize("name", CONFIGS)
async def test_status_reflects_real_checks(name, client, make_key, check):
    key = await make_key(**CONFIGS[name])
    await check(key)
    assert (await get_status(client, key))["remaining"] == 2
    await check(key)
    assert (await get_status(client, key))["remaining"] == 1


async def test_status_unknown_key_returns_404(client):
    r = await client.get("/status/no-such-key/u1")
    assert r.status_code == 404