import asyncio


async def test_allows_up_to_limit_then_denies(make_key, check):
    key = await make_key(algorithm="sliding_window", limit=5, window_seconds=2)
    results = [await check(key) for _ in range(6)]
    assert [r["allowed"] for r in results] == [True] * 5 + [False]


async def test_window_slides(make_key, check):
    key = await make_key(algorithm="sliding_window", limit=2, window_seconds=1)
    await check(key)
    await check(key)
    assert (await check(key))["allowed"] is False
    await asyncio.sleep(1.1)
    assert (await check(key))["allowed"] is True


async def test_edge_burst_is_denied(make_key, check):
    """The case fixed window lets through: 1 request at t=0, 4 at t=1.5, 5 at t~2.2."""
    key = await make_key(algorithm="sliding_window", limit=5, window_seconds=2)
    await check(key)
    await asyncio.sleep(1.5)
    for _ in range(4):
        await check(key)
    await asyncio.sleep(0.7)  # the t=0 entry has now left the window
    results = [await check(key) for _ in range(5)]
    assert [r["allowed"] for r in results] == [True, False, False, False, False]