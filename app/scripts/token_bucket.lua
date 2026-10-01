-- KEYS[1] = hash {tokens, last_refill}
-- ARGV[1] = capacity, ARGV[2] = refill rate (tokens per second), ARGV[3] = cost
-- Returns {allowed, remaining, retry_after_ms, reset_at_ms}

local capacity = tonumber(ARGV[1])
local rate_ms  = tonumber(ARGV[2]) / 1000   -- tokens per millisecond
local cost     = tonumber(ARGV[3])

local t = redis.call('TIME')
local now_ms = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)

local data   = redis.call('HMGET', KEYS[1], 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last   = tonumber(data[2])

-- First request for this key: start with a full bucket
if tokens == nil then
  tokens = capacity
  last = now_ms
end

-- Refill for the time that has passed, never above capacity
local elapsed = math.max(now_ms - last, 0)
tokens = math.min(capacity, tokens + elapsed * rate_ms)

local allowed = 0
local retry = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
else
  retry = math.ceil((cost - tokens) / rate_ms)
end

-- Save even on deny: tokens already includes the refill up to now,
-- so last_refill must move forward or the same time would be counted twice
redis.call('HSET', KEYS[1], 'tokens', tokens, 'last_refill', now_ms)

-- Idle buckets are removed once they would be full again anyway
redis.call('PEXPIRE', KEYS[1], math.ceil(capacity / rate_ms))

local reset = now_ms + math.ceil((capacity - tokens) / rate_ms)
return {allowed, math.floor(tokens), retry, reset}