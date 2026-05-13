---
category: technologies
created: 2026-05-13
updated: 2026-05-13
tags: [resilience, fault-tolerance, api-client, production-ready]
related: [rate-limiting.md, retry-logic.md, error-handling.md]
confidence: high
---

# Circuit Breaker Pattern

## Overview

Circuit Breaker is a **fault tolerance pattern** that prevents cascading failures by stopping requests to failing services. When a service fails repeatedly, the circuit "opens" and blocks further requests, giving the service time to recover.

**Source:** https://github.com/High-Functioning-Solutions/hfs-location-client

**Quality Score:** 85.0/100

**Adopted:** 2026-05-13 (Content Gap Analysis Agent)

## How It Works

### Three States

```
CLOSED (normal operation)
  ↓ (failures exceed threshold)
OPEN (blocking requests)
  ↓ (timeout expires)
HALF_OPEN (testing recovery)
  ↓ (success) → CLOSED
  ↓ (failure) → OPEN
```

### State Transitions

1. **CLOSED → OPEN**
   - Trigger: Failure count ≥ threshold (default: 5)
   - Action: Block all requests
   - Duration: Until recovery timeout (default: 60s)

2. **OPEN → HALF_OPEN**
   - Trigger: Recovery timeout expires
   - Action: Allow 1 test request
   - Purpose: Check if service recovered

3. **HALF_OPEN → CLOSED**
   - Trigger: Test request succeeds
   - Action: Resume normal operation
   - Reset: Failure count = 0

4. **HALF_OPEN → OPEN**
   - Trigger: Test request fails
   - Action: Block requests again
   - Duration: Another recovery timeout

## Implementation

### Key Parameters

```python
failure_threshold: int = 5      # Failures before opening
recovery_timeout: float = 60.0  # Seconds before testing recovery
```

### Core Methods

```python
class SyncCircuitBreaker:
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        
    def _record_success(self) -> None:
        """Record successful call, reset failure count."""
        
    def _record_failure(self) -> None:
        """Record failed call, open circuit if threshold exceeded."""
```

### Usage Example

```python
from circuit_breaker import SyncCircuitBreaker, CircuitOpenError

# Create circuit breaker
breaker = SyncCircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)

# Wrap API call
try:
    response = breaker.call(api_client.fetch, url)
except CircuitOpenError:
    # Circuit is open, service is down
    return cached_response
```

## Benefits

### 1. Prevents Cascading Failures

**Problem:** Service A calls Service B. Service B is down. Service A keeps trying, exhausting resources.

**Solution:** Circuit breaker stops calls to Service B after threshold, preventing Service A from wasting resources.

**Impact:** System remains stable even when dependencies fail.

### 2. Faster Failure Detection

**Problem:** Waiting for timeouts on every request (30s × 100 requests = 50 minutes)

**Solution:** Circuit opens after 5 failures, immediately rejecting further requests.

**Impact:** Fail fast (milliseconds instead of seconds), better UX.

### 3. Automatic Recovery

**Problem:** Manual intervention needed to resume calls after service recovers.

**Solution:** Circuit automatically tests recovery after timeout, resumes if successful.

**Impact:** Self-healing system, no manual intervention.

### 4. Resource Protection

**Problem:** Threads/connections blocked waiting for failing service.

**Solution:** Circuit breaker rejects requests immediately, freeing resources.

**Impact:** System can handle other work while dependency is down.

## When to Use

### ✅ Use Circuit Breaker When:

1. **External API calls** (third-party services)
2. **Microservices communication** (service-to-service)
3. **Database connections** (prevent connection pool exhaustion)
4. **Network operations** (any I/O that can fail)
5. **High-traffic systems** (where cascading failures are costly)

### ❌ Don't Use Circuit Breaker When:

1. **Internal function calls** (no network involved)
2. **One-time operations** (not repeated)
3. **User input validation** (not a service failure)
4. **Low-traffic systems** (overhead not justified)
5. **Already have retry logic** (circuit breaker complements, not replaces)

## Best Practices

### 1. Tune Parameters for Your Use Case

```python
# High-traffic API (fail fast)
breaker = SyncCircuitBreaker(
    failure_threshold=3,      # Open quickly
    recovery_timeout=30.0     # Test recovery soon
)

# Low-traffic API (more tolerant)
breaker = SyncCircuitBreaker(
    failure_threshold=10,     # More failures allowed
    recovery_timeout=120.0    # Wait longer before testing
)
```

### 2. Combine with Retry Logic

```python
# Retry with exponential backoff
for attempt in range(3):
    try:
        return breaker.call(api_client.fetch, url)
    except CircuitOpenError:
        # Circuit open, don't retry
        raise
    except Exception as e:
        # Other error, retry with backoff
        if attempt < 2:
            time.sleep(2 ** attempt)
        else:
            raise
```

### 3. Monitor Circuit State

```python
# Log state changes
breaker.on_open = lambda: logger.warning("Circuit opened")
breaker.on_close = lambda: logger.info("Circuit closed")
breaker.on_half_open = lambda: logger.info("Circuit half-open")

# Expose metrics
metrics.gauge("circuit_breaker.state", breaker.state.value)
metrics.counter("circuit_breaker.failures", breaker.failure_count)
```

### 4. Provide Fallback Behavior

```python
try:
    response = breaker.call(api_client.fetch, url)
except CircuitOpenError:
    # Fallback to cache
    response = cache.get(url)
    if response is None:
        # Fallback to default
        response = default_response
```

## Common Pitfalls

### 1. Threshold Too Low

**Problem:** Circuit opens on transient errors, blocking valid requests.

**Solution:** Set threshold ≥5 for most use cases, monitor false positives.

### 2. Timeout Too Short

**Problem:** Circuit tests recovery before service is ready, stays open.

**Solution:** Set timeout ≥60s for most services, adjust based on recovery time.

### 3. No Fallback

**Problem:** Circuit opens, application crashes because no fallback.

**Solution:** Always provide fallback (cache, default, error message).

### 4. Shared Circuit Breaker

**Problem:** One failing endpoint opens circuit for all endpoints.

**Solution:** Use separate circuit breakers per endpoint/service.

```python
# ❌ BAD: Shared circuit breaker
breaker = SyncCircuitBreaker()
breaker.call(api.endpoint1)  # Fails
breaker.call(api.endpoint2)  # Blocked (even if healthy)

# ✅ GOOD: Separate circuit breakers
breaker1 = SyncCircuitBreaker()
breaker2 = SyncCircuitBreaker()
breaker1.call(api.endpoint1)  # Fails
breaker2.call(api.endpoint2)  # Still works
```

## Performance Impact

### Overhead

- **Closed state:** ~1-2 microseconds per call (negligible)
- **Open state:** ~0.1 microseconds per call (immediate rejection)
- **Half-open state:** Same as closed (1 test request)

### Memory

- **Per circuit breaker:** ~100 bytes (state + counters + timestamp)
- **100 circuit breakers:** ~10 KB (negligible)

### Benefit

- **Prevents:** Seconds of wasted time per failed request
- **Saves:** Thread/connection resources
- **Improves:** System stability and UX

**ROI:** 1000x+ (microseconds overhead vs seconds saved)

## Related Patterns

### 1. Retry Logic

**Relationship:** Complementary

**Use together:**
- Retry handles transient errors (network blip)
- Circuit breaker handles persistent failures (service down)

### 2. Rate Limiting

**Relationship:** Complementary

**Use together:**
- Rate limiting prevents overloading service
- Circuit breaker handles when service is already overloaded

### 3. Timeout

**Relationship:** Prerequisite

**Use together:**
- Timeout detects slow/hanging requests
- Circuit breaker counts timeouts as failures

### 4. Bulkhead

**Relationship:** Complementary

**Use together:**
- Bulkhead isolates resources per service
- Circuit breaker stops calls to failing service

## Metrics to Track

### Circuit State

```python
# Gauge: Current state (0=closed, 1=open, 2=half_open)
metrics.gauge("circuit_breaker.state", breaker.state.value)
```

### Failure Count

```python
# Counter: Total failures
metrics.counter("circuit_breaker.failures", breaker.failure_count)
```

### State Transitions

```python
# Counter: Times circuit opened
metrics.counter("circuit_breaker.opened", 1)

# Counter: Times circuit closed
metrics.counter("circuit_breaker.closed", 1)
```

### Rejected Requests

```python
# Counter: Requests blocked by open circuit
metrics.counter("circuit_breaker.rejected", 1)
```

## Testing

### Unit Tests

```python
def test_circuit_opens_after_threshold():
    breaker = SyncCircuitBreaker(failure_threshold=3)
    
    # Fail 3 times
    for _ in range(3):
        with pytest.raises(Exception):
            breaker.call(failing_function)
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN
    
    # Next call should raise CircuitOpenError
    with pytest.raises(CircuitOpenError):
        breaker.call(failing_function)
```

### Integration Tests

```python
def test_circuit_recovers_after_timeout():
    breaker = SyncCircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1.0  # Short for testing
    )
    
    # Open circuit
    for _ in range(3):
        with pytest.raises(Exception):
            breaker.call(failing_function)
    
    # Wait for recovery timeout
    time.sleep(1.1)
    
    # Circuit should be half-open
    assert breaker.state == CircuitState.HALF_OPEN
    
    # Successful call should close circuit
    breaker.call(successful_function)
    assert breaker.state == CircuitState.CLOSED
```

## References

### Original Pattern

- **Book:** "Release It!" by Michael Nygard (2007)
- **Pattern:** Circuit Breaker (Chapter 5)

### Implementations

- **Python:** pybreaker, circuitbreaker, tenacity
- **Java:** Resilience4j, Hystrix (deprecated)
- **Go:** gobreaker, sony/gobreaker
- **JavaScript:** opossum, cockatiel

### Our Implementation

- **Source:** https://github.com/High-Functioning-Solutions/hfs-location-client
- **File:** `_sync_circuit_breaker.py`
- **Adopted:** 2026-05-13
- **Quality:** 85.0/100

---

**Last Updated:** 2026-05-13
**Next Review:** 2026-06-13
