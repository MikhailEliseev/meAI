# API Integration Patterns - Key Findings

## Architecture Pattern: Unified Client with Composition

```python
@dataclass
class UnifiedSEOClient:
    semrush: APIClient
    ahrefs: APIClient
    gsc: APIClient
    yandex: APIClient
    
    async def get_domain_metrics(self, domain: str) -> dict:
        tasks = [self._fetch_semrush(domain), ...]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._normalize_results(results)
```

**Key Principle:** `asyncio.gather(..., return_exceptions=True)` для graceful degradation

## Three-Layer Resilience Stack

1. **Circuit Breaker** (pybreaker) - fail fast during outages
2. **Retry with Exponential Backoff** (tenacity) - jitter prevents thundering herd
3. **Per-Attempt Timeout** - each retry gets own deadline

## Rate Limiting: Token Bucket Pattern

```python
@dataclass
class TokenBucket:
    capacity: int
    refill_rate: float  # tokens per second
    
    async def acquire(self, tokens: int = 1) -> float:
        # Proactive throttling - prevents 429s before they happen
```

**Production Note:** For distributed systems use Redis-based rate limiting

## Data Normalization: Schema-First with Pydantic

```python
class DomainMetrics(BaseModel):
    domain: str
    authority_score: Optional[float] = Field(None, ge=0, le=100)
    backlinks_total: Optional[int] = None
    source: str  # Which API provided this data
```

## Actionable Recommendations

1. ✅ Start with tenacity + pybreaker (90% of resilience needs)
2. ✅ Implement token buckets per API (prevents 429s)
3. ✅ Use Pydantic for normalization (type safety)
4. ✅ Monitor circuit breaker state (open = systemic issue)
5. ✅ Log retry attempts with structured data

## Production Checklist

- [ ] Circuit breaker per API (fail_max=5, reset_timeout=60s)
- [ ] Exponential backoff with jitter (initial=1s, max=30s)
- [ ] Per-attempt timeout (10s for SEO APIs)
- [ ] Token bucket matching API quotas
- [ ] Retry-After header parsing
- [ ] Unified schema with Pydantic validation
- [ ] Graceful degradation on API failure
- [ ] Structured logging for observability
