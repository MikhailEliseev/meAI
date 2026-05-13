# Teacher Agent v2.0 - Monitoring & Alerting System Added ✅

**Date:** 2026-05-13  
**Status:** COMPLETE

---

## Summary

Добавил критически важную систему мониторинга и алертов в спецификацию Teacher Agent v2.0.

**Spec Size:**
- Before: 3996 lines, 132 KB
- After: 4508 lines, 150 KB
- Added: +512 lines, +18 KB

**Time:** ~15 minutes

---

## Problem Statement

**User Requirement:**
> "Если EXO или какой-то из Endpoints для обучения недоступен, нужен сразу алерт пользователю через оператора. Потому что иначе у нас система не будет расти, а я не буду знать, что Teacher недополучает данные."

**Why Critical:**
- Без Exa API → нет deep research → нет best practices
- Без GitHub API → нет repo discovery → нет новых паттернов
- Без данных → система не растёт → конкурентное преимущество теряется
- **Silent failure = катастрофа** (пользователь не знает, что система не учится)

---

## Solution: Section 9 - Monitoring & Alerting System

### 9.1 Monitored Endpoints

**Critical (must be up):**
1. **Exa API** - deep research (web_search_exa, deep_researcher_start)
2. **GitHub API** - repo discovery (search, get details)
3. **Event Bus** - communication with Operator
4. **Obsidian** - audit trail

**Optional (fallback available):**
5. **Brave API** - fallback for Exa

### 9.2 HealthMonitor Component

```python
class HealthMonitor:
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        self.event_bus = event_bus
        self.obsidian = obsidian
        self.alert_threshold = 3  # Alert after 3 consecutive failures
    
    async def check_all_endpoints(self) -> SystemHealth:
        """Check health of all critical endpoints."""
        # Check each endpoint
        # Calculate overall status
        # Send alerts if needed
        return SystemHealth(
            overall_status="healthy" | "degraded" | "critical",
            can_research=True/False,
            can_discover_github=True/False,
            can_alert=True/False
        )
```

**Health Checks:**
- Exa API: quick search test
- GitHub API: quick repo search test
- Brave API: quick search test
- Event Bus: publish test event
- Obsidian: write test log

**Frequency:**
- Before each learning cycle: Always
- During learning cycle: After each major step
- Periodic: Every 1 hour (background)

### 9.3 Alert System

**Alert Threshold:**
- 3 consecutive failures → Send alert
- 5 consecutive failures → Mark as critical
- 10 consecutive failures → Disable endpoint (use fallback)

**Alert Flow:**
```
HealthMonitor detects 3+ failures
   ↓
Sends P0/P1 event to Operator via Event Bus
   ↓
Operator receives event
   ↓
Notifies user via:
- Telegram (if configured)
- Email (if configured)
- Console output (always)
```

**Alert Message Format:**
```
🚨 Teacher Agent Alert: CRITICAL

Endpoint: exa_api
Status: down
Consecutive failures: 3
Last success: 2026-05-13 14:00:00
Error: Connection timeout

Impact on system:
❌ Cannot perform deep research
✅ Can still discover GitHub repos
✅ Can send alerts

Overall system status: DEGRADED

Action required:
1. Check exa_api availability
2. Verify API keys/credentials
3. Check rate limits
4. Review error logs in Obsidian vault

⚠️ System growth is blocked until this is resolved!
```

### 9.4 System Health States

**Healthy:**
- All critical endpoints up
- System can research + discover GitHub
- No alerts

**Degraded:**
- 1 critical endpoint down
- System can operate with limitations
- Warning alert sent
- Fallback strategies activated

**Critical:**
- 2+ critical endpoints down
- System cannot operate
- Critical alert sent
- Learning workflow aborted

### 9.5 Fallback Strategies

**If Exa API down:**
- Use Brave Search API (if available)
- Use cached research from previous cycles
- Skip deep research, proceed with GitHub only

**If GitHub API down:**
- Use cached repository list
- Skip new repo discovery
- Focus on improving existing subagents

**If both Exa and GitHub down:**
- CRITICAL: Cannot proceed
- Alert user immediately
- System growth blocked

**If Event Bus down:**
- CRITICAL: Cannot communicate
- Log to Obsidian as last resort
- System isolated

### 9.6 Integration with TeacherAgent

```python
class TeacherAgent:
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        # Existing components
        self.research_orchestrator = ResearchOrchestrator()
        self.skill_orchestrator = SkillExtractionOrchestrator()
        
        # NEW: Health monitoring
        self.health_monitor = HealthMonitor(event_bus, obsidian)
    
    async def learn_from_github(self, subagent_name: str) -> LearningResult:
        # 1. Check health BEFORE starting
        health = await self.health_monitor.check_all_endpoints()
        
        if health.overall_status == "critical":
            # Cannot proceed - alert and abort
            await self._handle_critical_health(health)
            raise SystemHealthError("Critical endpoints down")
        
        if health.overall_status == "degraded":
            # Can proceed with limitations - log warning
            await self.obsidian.log(f"Starting with degraded health: {health}")
        
        # 2. Proceed with learning workflow
        # 3. Check health after each major step
        # 4. Handle health degradation during execution
```

### 9.7 Operator Integration

```python
class Operator:
    async def handle_teacher_alert(self, event: Event):
        """Handle alerts from Teacher Agent."""
        severity = event.data["severity"]
        message = event.data["message"]
        
        # Log to Operator's vault
        await self.obsidian.log(f"Teacher Alert: {severity}", metadata=event.data)
        
        # Notify user
        if severity == "CRITICAL":
            await self._notify_user_urgent(message)  # Telegram/Email/Console
        else:
            await self._add_to_digest(message)  # Daily digest
```

---

## Key Features

**1. Proactive Monitoring:**
- Checks endpoints before and during learning
- Detects failures early (3 consecutive failures)
- No silent failures

**2. Clear Alerts:**
- Severity: CRITICAL vs WARNING
- Impact: what's broken, what still works
- Action items: what user needs to do
- Context: error messages, timestamps

**3. Fallback Strategies:**
- Brave API if Exa down
- Cached data if APIs down
- Graceful degradation

**4. User Transparency:**
- User always knows system health
- No surprise "why isn't Teacher working?" moments
- Clear action items in alerts

**5. Multiple Notification Channels:**
- Telegram (if configured)
- Email (if configured)
- Console output (always)

---

## Success Criteria

**System Health:**
- ✅ All critical endpoints monitored
- ✅ Alerts sent within 1 minute of failure threshold
- ✅ User notified via Operator
- ✅ Fallback strategies implemented
- ✅ No silent failures

**User Experience:**
- ✅ User knows immediately when system cannot grow
- ✅ Clear action items in alerts
- ✅ No surprise failures
- ✅ Transparency: sees all endpoint health

---

## Metrics

**Health Metrics:**
- Endpoint uptime percentage (target: 99%+)
- Average response time per endpoint
- Consecutive failure count
- Time since last successful check

**Alert Metrics:**
- Alerts sent per day
- Alert severity distribution
- Time to resolution
- False positive rate

**Impact Metrics:**
- Learning cycles blocked due to failures
- Subagents not updated due to data unavailability
- System growth rate (with vs without issues)

---

## Example Alert Scenarios

**Scenario 1: Exa API Down**
```
🚨 Teacher Agent Alert: CRITICAL

Endpoint: exa_api
Status: down
Consecutive failures: 3
Error: Connection timeout

Impact:
❌ Cannot perform deep research
✅ Can still discover GitHub repos

Action:
1. Check Exa API status
2. Verify API key
3. Check rate limits

Fallback: Using Brave API for research
```

**Scenario 2: GitHub API Rate Limit**
```
⚠️ Teacher Agent Alert: WARNING

Endpoint: github_api
Status: degraded
Consecutive failures: 3
Error: Rate limit exceeded (60/hour)

Impact:
❌ Cannot discover new GitHub repos
✅ Can still perform deep research

Action:
1. Add GITHUB_TOKEN to .env (5000 req/hour)
2. Or wait 1 hour for rate limit reset

Fallback: Using cached repository list
```

**Scenario 3: Both Exa and GitHub Down**
```
🚨 Teacher Agent Alert: CRITICAL

System status: CRITICAL

Endpoints down:
- exa_api: Connection timeout
- github_api: Service unavailable

Impact:
❌ Cannot perform deep research
❌ Cannot discover GitHub repos
❌ SYSTEM GROWTH IS BLOCKED

Action required immediately:
1. Check Exa API status
2. Check GitHub API status
3. Verify API keys
4. Review error logs

Learning workflow aborted.
```

---

## Implementation Notes

**Phase 1.0 (Research Layer):**
- Implement HealthMonitor
- Implement endpoint health checks
- Implement alert system

**Phase 1.5 (Skill Layer):**
- Integrate health checks into learning workflow
- Add fallback strategies

**Phase 2+ (Full Workflow):**
- Add periodic health checks (every 1 hour)
- Add health dashboard in Obsidian
- Add metrics tracking

---

## Next Steps

1. ✅ Monitoring & Alerting System added to spec
2. ⏳ Final user approval (Task #25)
3. ⏳ Begin Phase 1.0 implementation (3-4 hours)
4. ⏳ Begin Phase 1.5 implementation (4-5 hours)
5. ⏳ Begin Phase 2+ implementation (8-12 hours)

---

## Recommendation

**READY FOR FINAL APPROVAL** ✅

Спецификация теперь включает критически важную систему мониторинга:
- ✅ Все endpoints мониторятся
- ✅ Алерты отправляются через Operator
- ✅ Пользователь всегда знает, когда система не может расти
- ✅ Fallback стратегии для graceful degradation
- ✅ Нет silent failures

Можно начинать implementation после финального approval.

---

**Created:** 2026-05-13 17:01 GMT+3  
**Changes:** +512 lines, +18 KB  
**New Section:** 9 (Monitoring & Alerting System)  
**Status:** ✅ Complete - Ready for Final Approval
