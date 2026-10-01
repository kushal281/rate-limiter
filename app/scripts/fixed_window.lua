-- KEYS[1] = counter key
-- ARGV[1] = limit, ARGV[2] = window seconds, ARGV[3] = cost
-- Returns {allowed, remaining, retry_after_ms, reset_at_ms}

local limit  = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local cost   = tonumber(ARGV[3])

local current = tonumber(redis.call('GET', KEYS[1]) or '0')

-- Redis clock, not the app server's clock
local t = redis.call('TIME')
local now_ms = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)

-- Over the limit: deny and don't consume
if current + cost > limit then
  local ttl = math.max(redis.call('PTTL', KEYS[1]), 0)
  return {0, limit - current, ttl, now_ms + ttl}
end

-- Allowed: consume, and start the window on the first request
current = redis.call('INCRBY', KEYS[1], cost)
if current == cost then
  redis.call('EXPIRE', KEYS[1], window)
end
local ttl = redis.call('PTTL', KEYS[1])
return {1, limit - current, 0, now_ms + ttl}