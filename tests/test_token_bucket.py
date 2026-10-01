import asyncio


async def test_burst_up_to_capacity_then_denies(make_key, check):
    key = await make_key(algorithm="token_bucket", limit=5, window_seconds=10, burst=3)
    results = [await check(key) for _ in range(4)]
    assert [r["allowed"] for r in results] == [True, True, True, False]


async def test_steady_refill(make_key, check):
    # 10 tokens per 5 s = 2 tokens/s, capacity 2
    key = await make_key(algorithm="token_bucket", limit=10, window_seconds=5, burst=2)
    await check(key)
    await check(key)
    assert (await check(key))["allowed"] is False
    await asyncio.sleep(0.6)  # ~1.2 tokens back
    assert (await check(key))["allowed"] is True
    assert (await check(key))["allowed"] is False


async def test_cost_spends_multiple_tokens(make_key, check):
    key = await make_key(algorithm="token_bucket", limit=5, window_seconds=100, burst=5)
    first = await check(key, cost=5)
    assert first["allowed"] is True and first["remaining"] == 0
    assert (await check(key))["allowed"] is False


async def test_refill_is_capped_at_capacity(make_key, check):
    # 2 tokens/s, capacity 2. After a long idle the bucket must hold 2, not 4.
    key = await make_key(algorithm="token_bucket", limit=2, window_seconds=1, burst=2)
    await check(key)
    await check(key)
    await asyncio.sleep(2)  # uncapped, this would refill 4 tokens
    result = await check(key)
    assert result["allowed"] is True
    assert result["remaining"] == 1  # capped: 2 - 1. Uncapped would give 3.