# Circuit Breaker Pattern

**Date:** 2026-05-02 23:06  
**Type:** Improvement Idea

## Problem

Currently, when a service fails (e.g., Perplexity API down), we keep retrying and hitting it. This:
- Wastes resources on failed requests
- Delays error detection
- Can cause cascade failures across system

## Idea

Implement Circuit Breaker pattern:
- **Closed** - Normal operation, requests go through
- **Open** - After N failures, stop sending requests (circuit "opens")
- **Half-Open** - After timeout, try one request to test if service recovered

## Benefits

- Prevents cascade failures
- Faster failure detection
- Reduces load on failing services
- Industry standard (Netflix Hystrix, AWS)

## Implementation

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.state = "closed"
        self.last_failure_time = None
    
    async def call(self, func):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitOpenError("Circuit breaker is open")
        
        try:
            result = await func()
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise
```

## Where to Apply

- Perplexity API calls (Researcher)
- Teacher queries (Qdrant)
- Event Bus message publishing
- Database connections

## Priority

Medium - improves resilience, but not critical (we have retries)

## Related

- Exponential backoff (already noted)
- Timeout management (already implemented)
- Error handling (already implemented)

## References

- Netflix Hystrix pattern
- AWS Well-Architected Framework
- Martin Fowler's Circuit Breaker article
