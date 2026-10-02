-- KEYS[1] = zset of request timestamps
-- ARGV[1] = limit, ARGV[2] = window seconds
-- Read-only. Returns {remaining, reset_at_ms}

local limit     = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2]) * 1000

local t = redis.call('TIME')
local now_ms = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)

local min = '(' .. (now_ms - window_ms)
local count = redis.call('ZCOUNT', KEYS[1], min, '+inf')

local oldest = redis.call('ZRANGEBYSCORE', KEYS[1], min, '+inf', 'WITHSCORES', 'LIMIT', 0, 1)
local reset = now_ms
if oldest[2] then reset = tonumber(oldest[2]) + window_ms end

return {math.max(limit - count, 0), reset}