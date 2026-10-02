-- KEYS[1] = counter key
-- ARGV[1] = limit
-- Read-only. Returns {remaining, reset_at_ms}

local limit = tonumber(ARGV[1])

local t = redis.call('TIME')
local now_ms = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)

local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local ttl = math.max(redis.call('PTTL', KEYS[1]), 0)  -- PTTL is -2 if no window is active

return {math.max(limit - current, 0), now_ms + ttl}