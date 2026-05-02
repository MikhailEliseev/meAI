# Exponential Backoff for Retries

**Date:** 2026-05-02 22:55  
**Type:** Improvement Idea

## Problem

Currently, retry logic uses fixed 5-second delay between attempts. This can:
- Overload systems during outages (all retries hit at same time)
- Waste time on transient failures (5 seconds might be too long)
- Not adapt to different failure types

## Idea

Implement exponential backoff with jitter:
- 1st retry: 1-2 seconds
- 2nd retry: 2-4 seconds  
- 3rd retry: 4-8 seconds

Add jitter to prevent thundering herd.

## Benefits

- Reduces load during outages
- Faster recovery from transient failures
- Industry standard pattern (AWS, Google use it)

## Implementation

Update `operator.py`:
```python
RETRY_DELAYS = [1, 2, 4]  # Base delays in seconds
JITTER_FACTOR = 0.5  # ±50% jitter

async def _retry_subtask(self, subtask, retry_count):
    base_delay = RETRY_DELAYS[retry_count - 1]
    jitter = random.uniform(-JITTER_FACTOR, JITTER_FACTOR)
    delay = base_delay * (1 + jitter)
    await asyncio.sleep(delay)
    # ... rest of retry logic
```

## Priority

High - improves system resilience

## Related

- Circuit breaker pattern (future improvement)
- Timeout management (already implemented)
- Error handling (already implemented)
