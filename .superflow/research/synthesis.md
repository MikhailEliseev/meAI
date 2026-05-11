# Research Synthesis: Keyword Research Agent Implementation

## Unified Technical Recommendations

### 1. Architecture Pattern

**Unified Client with Three-Layer Resilience:**
```python
@dataclass
class KeywordResearchClient:
    semrush: APIClient
    ahrefs: APIClient
    gsc: APIClient
    yandex: APIClient
    
    # Layer 1: Circuit Breaker (pybreaker)
    # Layer 2: Retry with Exponential Backoff (tenacity)
    # Layer 3: Per-Attempt Timeout
    
    async def collect_keywords(self, domain: str) -> dict:
        tasks = [self._fetch_semrush(domain), ...]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._normalize_and_prioritize(results)
```

### 2. Keyword Prioritization Formula

**Production-Ready Implementation:**
```python
def calculate_priority(
    volume: int,
    difficulty: int,
    intent_score: int,  # 1-5
    current_position: int,
    serp_features: list,
    compliance_risk: int  # NEW: 1-25 from compliance check
) -> dict:
    # Normalize (0-100)
    vol_norm = min(100, (math.log10(volume) / math.log10(100000)) * 100)
    diff_norm = 100 - difficulty
    intent_norm = (intent_score / 5) * 100
    pos_norm = max(0, 100 - (current_position * 3))
    
    # Weighted score (medical marketing weights)
    base_score = (
        vol_norm * 0.20 +      # 20% volume
        intent_norm * 0.30 +   # 30% intent (HIGH for medical)
        diff_norm * 0.25 +     # 25% difficulty
        pos_norm * 0.15 +      # 15% position
        trend_norm * 0.10      # 10% trend
    )
    
    # SERP penalties
    serp_penalty = sum(penalties.get(f, 0) for f in serp_features)
    
    # Compliance penalty (NEW)
    compliance_penalty = 0
    if compliance_risk >= 20:  # CRITICAL
        compliance_penalty = 1.0  # Block completely
    elif compliance_risk >= 15:  # HIGH
        compliance_penalty = 0.5  # Reduce priority by 50%
    elif compliance_risk >= 8:   # MEDIUM
        compliance_penalty = 0.2  # Reduce priority by 20%
    
    final_score = base_score * (1 - min(0.8, serp_penalty)) * (1 - compliance_penalty)
    
    # Classify
    if final_score >= 80: priority = "P0"
    elif final_score >= 65: priority = "P1"
    elif final_score >= 45: priority = "P2"
    elif final_score >= 25: priority = "P3"
    else: priority = "SKIP"
    
    return {'score': round(final_score, 1), 'priority': priority}
```

### 3. Medical Compliance Integration

**Automated Compliance Checking:**
```python
async def check_keyword_compliance(keyword: str, context: dict) -> dict:
    # 1. FDA enforcement check (openFDA API)
    fda_violations = await check_fda_enforcement(keyword)
    
    # 2. Language pattern check (prohibited terms)
    prohibited_patterns = check_prohibited_language(keyword)
    
    # 3. Calculate risk score (Likelihood × Severity)
    risk_score = calculate_risk_score(fda_violations, prohibited_patterns)
    
    return {
        'risk_score': risk_score,  # 1-25
        'risk_level': classify_risk(risk_score),  # CRITICAL/HIGH/MEDIUM/LOW
        'violations': fda_violations,
        'flags': prohibited_patterns
    }
```

## Implementation Priorities

### Phase 1: Core Infrastructure (Sprint 1)
1. ✅ Unified API client with three-layer resilience
2. ✅ Token bucket rate limiting per API
3. ✅ Pydantic schemas for data normalization
4. ✅ Basic keyword prioritization formula

### Phase 2: API Integrations (Sprint 2-3)
**Parallel Waves:**
- Wave 1: SEMrush + Ahrefs (keyword data, difficulty)
- Wave 2: Google Search Console + Yandex Webmaster (positions)
- Wave 3: Yandex Wordstat + Google Keyword Planner (volume)

### Phase 3: Medical Compliance (Sprint 4)
1. ✅ openFDA API integration
2. ✅ Prohibited language detection
3. ✅ Risk scoring framework
4. ✅ Compliance penalty in prioritization

### Phase 4: Testing & Deployment (Sprint 5)
1. ✅ Unit tests (80%+ coverage)
2. ✅ Integration tests (Event Bus, Obsidian, DB)
3. ✅ E2E tests (full cycle with real APIs)
4. ✅ Performance benchmarks

## Risk Mitigation

### High-Risk Areas
1. **API Rate Limits** → Token bucket + circuit breaker
2. **API Costs** → Quota monitoring + alerts
3. **Medical Compliance** → Automated pre-publication checks
4. **Data Quality** → Multi-source validation + graceful degradation

### Mitigation Strategies
- Circuit breaker prevents cascading failures
- Graceful degradation (partial results > no results)
- Compliance checks block high-risk keywords
- Structured logging for debugging

## Success Metrics

**Performance:**
- Success rate > 95%
- Execution time < 15 min (standard analysis)
- API availability > 99%

**Quality:**
- Keywords found > 100 per project
- Compliance violations = 0
- Priority accuracy > 80% (validated by user feedback)

**Business:**
- Cost per analysis < $5 (API costs)
- Time saved vs manual research > 90%
- Actionable recommendations > 60%

## Next Steps

1. ✅ Research complete (3 agents, all findings synthesized)
2. → Brainstorming (expert panel for implementation approach)
3. → Product approval (present findings + brief to user)
4. → Specification (technical spec with dual-model review)
5. → Planning (implementation plan with sprint breakdown)
