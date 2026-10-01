-- KEYS[1] = zset of request timestamps
-- ARGV[1] = limit, ARGV[2] = window seconds, ARGV[3] = cost, ARGV[4] = unique request id
-- Returns {allowed, remaining, retry_after_ms, reset_at_ms}

local limit     = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2]) * 1000
local cost      = tonumber(ARGV[3])
local req_id    = ARGV[4]

local t = redis.call('TIME')
local now_ms = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)

-- 1. Drop entries that have left the window
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now_ms - window_ms)

local count = redis.call('ZCARD', KEYS[1])

-- 2. Over the limit: deny without consuming
if count + cost > limit then
  -- this many old entries must expire before the request fits
  local need = count + cost - limit
  local e = redis.call('ZRANGE', KEYS[1], need - 1, need - 1, 'WITHSCORES')
  local retry = window_ms  -- fallback (e.g. cost > limit)
  if e[2] then retry = tonumber(e[2]) + window_ms - now_ms end

  local o = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
  local reset = now_ms + window_ms
  if o[2] then reset = tonumber(o[2]) + window_ms end
  return {0, limit - count, retry, reset}
end

-- 3. Allowed: one entry per unit of cost
for i = 1, cost do
  redis.call('ZADD', KEYS[1], now_ms, req_id .. ':' .. i)
end
redis.call('PEXPIRE', KEYS[1], window_ms)  -- idle keys clean themselves up

local o = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
return {1, limit - count - cost, 0, tonumber(o[2]) + window_ms}