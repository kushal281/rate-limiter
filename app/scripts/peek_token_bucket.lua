-- KEYS[1] = hash {tokens, last_refill}
-- ARGV[1] = capacity, ARGV[2] = refill rate (tokens per second)
-- Read-only. Returns {remaining, reset_at_ms}

local capacity = tonumber(ARGV[1])
local rate_ms  = tonumber(ARGV[2]) / 1000

local t = redis.call('TIME')
local now_ms = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)

local data   = redis.call('HMGET', KEYS[1], 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last   = tonumber(data[2])

-- No bucket yet: a new key starts full
if tokens == nil then
  return {capacity, now_ms}
end

local elapsed = math.max(now_ms - last, 0)
tokens = math.min(capacity, tokens + elapsed * rate_ms)

return {math.floor(tokens), now_ms + math.ceil((capacity - tokens) / rate_ms)}