import asyncio


async def test_allows_up_to_limit_then_denies(make_key, check):
    key = await make_key(algorithm="fixed_window", limit=5, window_seconds=2)
    results = [await check(key) for _ in range(6)]
    assert [r["allowed"] for r in results] == [True] * 5 + [False]
    assert results[0]["remaining"] == 4
    assert results[4]["remaining"] == 0
    assert results[5]["retry_after"] > 0


async def test_resets_after_window(make_key, check):
    key = await make_key(algorithm="fixed_window", limit=2, window_seconds=1)
    await check(key)
    await check(key)
    assert (await check(key))["allowed"] is False
    await asyncio.sleep(1.1)
    assert (await check(key))["allowed"] is True


async def test_cost_consumes_multiple_units(make_key, check):
    key = await make_key(algorithm="fixed_window", limit=5, window_seconds=5)
    first = await check(key, cost=3)
    assert first["allowed"] is True and first["remaining"] == 2
    second = await check(key, cost=3)  # needs 3, only 2 left
    assert second["allowed"] is False and second["remaining"] == 2