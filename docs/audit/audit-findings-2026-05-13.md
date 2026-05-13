# Global Audit Findings - 2026-05-13

**Status:** CRITICAL ISSUES FOUND  
**Audit Phase:** Phase 1 - Teacher Agent Deep Dive

---

## CRITICAL ISSUE #1: SkillSelector Only Extracts Generic Patterns

### Problem

**File:** `AIM/src/aim/teacher/skills/skill_selector.py`  
**Lines:** 60-65, 301-350

**Current Implementation:**
```python
self.pattern_signatures = {
    "circuit_breaker": ["CircuitBreaker", "pybreaker", "fail_max", "reset_timeout"],
    "retry": ["retry", "tenacity", "stop_after_attempt", "wait_exponential"],
    "rate_limiting": ["AsyncLimiter", "aiolimiter", "RateLimiter", "rate_limit"],
    "caching": ["cached", "aiocache", "@cache", "ttl"],
}
```

**What's Wrong:**
- SkillSelector only looks for 4 generic resilience patterns
- Does NOT extract domain-specific patterns (MCP server architecture, DataFrame-first design, UNIX philosophy, etc.)
- Violates CLAUDE.md rule: "Извлечение специфичных для домена паттернов"

### Evidence from Training Reports

**Ads Subagent (yandex-ads-mcp):**
- Found: 120 tools for Yandex Direct, Metrika, Wordstat
- Found: MCP server architecture pattern
- Found: API client pattern with retry/timeout
- **Extracted:** Only 1 skill (Retry with Exponential Backoff)
- **Missed:** MCP server architecture, 120 tools structure, environment configuration

**SEO Subagent (advertools):**
- Found: DataFrame-first design (universal interface)
- Found: Modular function design (UNIX philosophy)
- Found: Website crawling, sitemap parsing, robots.txt testing
- **Extracted:** Only 6 skills (4 Caching, 1 Rate Limiting, 1 Retry)
- **Missed:** DataFrame-first architecture, modular functions, domain-specific capabilities

**Analytics Subagent (PostHog):**
- Found: Production-ready analytics platform (34,459 stars)
- Found: Event-driven architecture
- Found: Real-time data processing
- **Extracted:** 1,030 skills (523 Caching, 415 Retry, 113 Rate Limiting)
- **Missed:** Event-driven architecture, real-time processing patterns, analytics-specific patterns

### Impact

**HIGH SEVERITY:**
- Teacher Agent is NOT learning domain-specific patterns
- Training reports document patterns but code doesn't extract them
- Subagents will NOT receive domain-specific knowledge
- System will have generic resilience but no domain expertise

### CLAUDE.md Violation

**Rule:** "Извлечение специфичных для домена паттернов"

**What it says:**
- ✅ Для КАЖДОГО субагента: индивидуальное deep research
- ✅ Клонирование и изучение кода из топовых репо
- ✅ **Извлечение специфичных для домена паттернов** ❌ VIOLATED
- ✅ Каждый субагент получает уникальное обучение

**Current State:**
- ✅ Domain-specific research: DONE (domain_queries dict)
- ✅ Cloning repos: DONE (clone_repo method)
- ❌ **Extracting domain-specific patterns: NOT DONE** (only 4 generic patterns)
- ❌ Unique training per subagent: PARTIALLY (research is unique, extraction is generic)

---

## CRITICAL ISSUE #2: Training Reports Document Patterns But Code Doesn't Extract Them

### Problem

**Training reports are DOCUMENTATION, not IMPLEMENTATION.**

**Example: Ads Subagent Report**
- Documents: "120 tools for Yandex Direct"
- Documents: "MCP server architecture"
- Documents: "API client pattern"
- **But SkillSelector code:** Only extracts 4 generic patterns

**Example: SEO Subagent Report**
- Documents: "DataFrame-first design"
- Documents: "Modular function design"
- Documents: "Website crawling patterns"
- **But SkillSelector code:** Only extracts 4 generic patterns

### Impact

**HIGH SEVERITY:**
- Reports look good but implementation is incomplete
- User thinks domain-specific patterns are extracted
- Reality: only generic patterns are extracted
- Gap between documentation and implementation

---

## CRITICAL ISSUE #3: No Domain-Specific Pattern Detection

### Problem

**SkillSelector needs domain-specific pattern signatures for each subagent type.**

**Missing Patterns:**

**Ads Subagent:**
- MCP server architecture (Server, stdio, tool registration)
- API client pattern (retry, timeout, error handling)
- Environment configuration (OAuth tokens, sandbox mode)
- Tool organization by service (Direct, Metrika, Wordstat)

**SEO Subagent:**
- DataFrame-first design (all functions return DataFrames)
- Modular function design (UNIX philosophy)
- Website crawling (spider, parser, extractor)
- Sitemap parsing (XML, URL extraction)
- robots.txt testing (rule checking)

**Analytics Subagent:**
- Event-driven architecture (event bus, handlers)
- Real-time data processing (streaming, aggregation)
- Multi-layer caching (Redis, in-memory, database)
- Analytics-specific patterns (metrics, dashboards, reports)

**Content Subagent:**
- LLM API integration (OpenAI, Anthropic, Gemini)
- Content generation workflows (prompt, generate, validate)
- Content optimization (SEO, readability, structure)

**Gap Detection Subagent:**
- SERP overlap analysis (keyword intersection)
- Keyword gap detection (competitor vs ours)
- Content gap analysis (missing topics)

**Prioritization Subagent:**
- MCDA methods (scoring, weighting, ranking)
- Priority queue implementation (Redis-based)
- Scoring algorithms (multi-criteria)

**Social Subagent:**
- Telegram Bot API integration (handlers, commands)
- Rate limiting for API compliance (30 msg/sec)
- Multi-platform support (Telegram, VK, etc.)

### Impact

**HIGH SEVERITY:**
- SkillSelector cannot extract domain-specific patterns
- Training is incomplete
- Subagents will not learn domain expertise

---

## Root Cause Analysis

### Why This Happened

1. **SkillSelector was designed for generic patterns only**
   - Initial implementation focused on resilience patterns
   - No consideration for domain-specific patterns

2. **Training reports are documentation, not implementation**
   - Reports document what was FOUND
   - Code extracts what it's PROGRAMMED to extract
   - Gap between documentation and implementation

3. **No domain-specific pattern signatures**
   - pattern_signatures dict only has 4 generic patterns
   - No domain-specific signatures for each subagent type

### What Needs to Change

1. **Add domain-specific pattern signatures**
   - Create domain_pattern_signatures dict
   - Map each subagent type to its domain-specific patterns
   - Update _detect_patterns() to check domain patterns

2. **Extract domain-specific patterns**
   - Detect MCP server architecture
   - Detect DataFrame-first design
   - Detect API client patterns
   - Detect domain-specific capabilities

3. **Align training reports with implementation**
   - Reports should reflect what code ACTUALLY extracts
   - Or code should extract what reports DOCUMENT

---

## Recommended Fix

### Phase 1: Add Domain-Specific Pattern Signatures (2 hours)

**File:** `AIM/src/aim/teacher/skills/skill_selector.py`

**Add:**
```python
self.domain_pattern_signatures = {
    "ads": {
        "mcp_server": ["mcp.server.Server", "stdio", "@server.tool"],
        "api_client": ["httpx.AsyncClient", "timeout=", "headers="],
        "oauth": ["OAuth", "token", "refresh_token"],
    },
    "seo": {
        "dataframe_first": ["pd.DataFrame", "return df", "to_frame()"],
        "modular_functions": ["def crawl_", "def parse_", "def extract_"],
        "sitemap": ["sitemap.xml", "urlset", "loc"],
    },
    "analytics": {
        "event_driven": ["event_bus", "emit", "on("],
        "real_time": ["stream", "aggregate", "window"],
        "metrics": ["metric", "gauge", "counter", "histogram"],
    },
    # ... etc for all subagents
}
```

**Update _detect_patterns():**
```python
def _detect_patterns(self, content: str, tree: ast.AST, subagent_type: str = None) -> dict:
    patterns = {}
    
    # Generic patterns (existing)
    # ...
    
    # Domain-specific patterns (new)
    if subagent_type and subagent_type in self.domain_pattern_signatures:
        domain_patterns = self.domain_pattern_signatures[subagent_type]
        for pattern_name, signatures in domain_patterns.items():
            if self._has_pattern_from_signatures(content, signatures):
                patterns[f"{subagent_type}_{pattern_name}"] = {
                    "name": f"{subagent_type.title()} - {pattern_name.replace('_', ' ').title()}",
                    "description": self._get_domain_pattern_description(subagent_type, pattern_name),
                    "code": self._extract_pattern_code_from_signatures(content, signatures),
                    "quality_score": self._score_pattern(content, pattern_name),
                }
    
    return patterns
```

### Phase 2: Update extract_skills() to Pass Subagent Type (30 min)

**Update method signature:**
```python
async def extract_skills(self, repo_path: Path, subagent_type: str = None) -> list[Skill]:
    # ...
    detected_patterns = self._detect_patterns(content, tree, subagent_type)
    # ...
```

### Phase 3: Update Training Scripts (30 min)

**Update all training scripts to pass subagent_type:**
```python
skills = await selector.extract_skills(clone_path, subagent_type="ads")
```

### Phase 4: Re-train All Subagents (1 hour)

**Re-run training with domain-specific extraction:**
- Ads: Extract MCP server, API client, OAuth patterns
- SEO: Extract DataFrame-first, modular functions, crawling patterns
- Analytics: Extract event-driven, real-time, metrics patterns
- Content: Extract LLM API, content generation patterns
- Gap Detection: Extract SERP overlap, keyword gap patterns
- Prioritization: Extract MCDA, priority queue, scoring patterns
- Social: Extract Telegram Bot API, rate limiting, multi-platform patterns

### Phase 5: Verify Results (30 min)

**Check:**
- Skills extracted include domain-specific patterns
- Training reports match implementation
- Each subagent has unique domain patterns

---

## Timeline

**Total Estimated Time:** 4.5 hours

**Breakdown:**
- Phase 1: 2 hours (add domain-specific signatures)
- Phase 2: 30 min (update extract_skills)
- Phase 3: 30 min (update training scripts)
- Phase 4: 1 hour (re-train all subagents)
- Phase 5: 30 min (verify results)

---

## Priority

**CRITICAL - Must fix before continuing**

**Why:**
- Teacher Agent is core learning system
- Without domain-specific extraction, system has no domain expertise
- Training reports are misleading (document but don't implement)
- Violates CLAUDE.md fundamental rule

---

## Next Steps

1. **Stop current audit** - Fix this issue first
2. **Implement Phase 1-5** - Add domain-specific extraction
3. **Re-train all subagents** - With domain-specific patterns
4. **Resume audit** - After fix is complete

---

## Audit Status

**Phase 1: Teacher Agent Deep Dive** - ✅ COMPLETE (CRITICAL ISSUES FOUND)  
**Phase 2: Training Reports Review** - ⏸️ PAUSED (waiting for fix)  
**Phase 3: CLAUDE.md Compliance** - ⏸️ PAUSED (waiting for fix)  
**Phase 4: Architecture Consistency** - ⏸️ PAUSED (waiting for fix)  
**Phase 5: LLM Wiki Pattern** - ⏸️ PAUSED (waiting for fix)  
**Phase 6: Session Recovery** - ⏸️ PAUSED (waiting for fix)  
**Phase 7: Code Quality** - ⏸️ PAUSED (waiting for fix)

**Recommendation:** Fix CRITICAL ISSUE #1 before continuing audit.
