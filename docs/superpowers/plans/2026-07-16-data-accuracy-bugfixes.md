# Data Accuracy Bugfixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 6 critical + 8 warning bugs in data collection pipeline found during deep audit

**Architecture:** Sequential fixes to seo_auditor, firecrawl_enricher, instagram_enricher, competitor_matcher_v2, brand_resolver

**Tech Stack:** Python 3.11+, asyncio, httpx, Firecrawl API, Apify API, bo.nalog

## Global Constraints

- GOLDEN STATE: chat UI/UX не меняем
- Все fixes в production файлах на сервере aim (78.17.128.169)
- Деплой: rsync → docker build → restart
- Никаких новых зависимостей

---

### Task 1: Robots parser — consecutive User-agent lines

**Files:**
- Modify: `AIM/src/aim/services/lib/seo_auditor.py` lines 200-250 (`_parse_robots_for_ai`)

**Bug:** `current_agents = [agent]` overwrites instead of accumulating. `User-agent: GPTBot\nUser-agent: ClaudeBot\nDisallow: /` → only ClaudeBot gets the directive.

- [ ] **Step 1: Fix accumulation logic**

Replace `current_agents = [agent]` with `current_agents.append(agent)` and reset on blank lines:

```python
for line in lines:
    line_lower = line.strip().lower()
    if not line_lower:
        current_agents = []
        continue
    if line_lower.startswith("#"):
        continue
    if line_lower.startswith("user-agent:"):
        agent = line_lower.split(":", 1)[1].strip()
        current_agents.append(agent)
        blocks.setdefault(agent, [])
    elif line_lower.startswith(("disallow:", "allow:")) and current_agents:
        for agent in current_agents:
            blocks.setdefault(agent, []).append(line_lower)
```

- [ ] **Step 2: Deploy and test on IPHK**

- [ ] **Step 3: Commit**

---

### Task 2: Doctor heading regex — too permissive

**Files:**
- Modify: `AIM/src/aim/services/lib/firecrawl_enricher.py` line 320

**Bug:** `^#{3,4}\s+([А-ЯЁ][а-яё]+)` matches "Акции", "Контакты" → false doctor count.

- [ ] **Step 1: Tighten regex to require name-like pattern**

```python
# Was: headings = re.findall(r"^#{3,4}\s+([А-ЯЁ][а-яё]+)", markdown, re.MULTILINE)
headings = re.findall(r"^#{3,4}\s+([А-ЯЁ][а-яё]+ [А-ЯЁ]\.?\s*[А-ЯЁ]\.?[^#\n]{0,50})", markdown, re.MULTILINE)
```

- [ ] **Step 2: Deploy and test**

- [ ] **Step 3: Commit**

---

### Task 3: Instagram — remove duplicate Firecrawl search + private accounts

**Files:**
- Modify: `AIM/src/aim/services/lib/instagram_enricher.py` lines 236-250

**Bug 1:** `elif` branch calls `search_instagram_handle` again (wasted API call). **Bug 2:** No private account handling.

- [ ] **Step 1: Remove duplicate elif branch + add private check in _get_instagram_via_apify**

Remove the entire `elif use_apify_fallback and not handle:` block (it duplicates the search). In `_get_instagram_via_apify`, add:

```python
if p.get("privateProfile") or p.get("isPrivate"):
    return {"followers": None, "posts": None, "private": True}
```

- [ ] **Step 2: Deploy and test**

- [ ] **Step 3: Commit**

---

### Task 4: scraped_services type violation — add revenue_history field

**Files:**
- Modify: `AIM/src/aim/services/rusprofile/models.py` — add field
- Modify: `AIM/src/aim/services/competitor_matcher_v2.py:863` — use new field

**Bug:** `profile.scraped_services = dynamics.get("history", [])` stores list[dict] in a list[str] field.

- [ ] **Step 1: Add `revenue_history` to CompanyProfile**

```python
revenue_history: list[dict] = field(default_factory=list)  # multi-year revenue
```

- [ ] **Step 2: Replace scraped_services hack**

```python
# Was: profile.scraped_services = dynamics.get("history", [])
profile.revenue_history = dynamics.get("history", [])
```

- [ ] **Step 3: Deploy and test**

- [ ] **Step 4: Commit**

---

### Task 5: Brand resolver — aggregate timeout for website scrape

**Files:**
- Modify: `AIM/src/aim/services/brand_resolver.py` lines 281-351

**Bug:** Up to 100s per brand (4 sequential Firecrawl calls), no aggregate timeout.

- [ ] **Step 1: Wrap _scrape_inn_from_website in asyncio.wait_for**

```python
try:
    inn = await asyncio.wait_for(_scrape_inn_from_website(website_url), timeout=20)
except asyncio.TimeoutError:
    return None
```

- [ ] **Step 2: Parallelize candidate URL scrapes with as_completed**

Replace the sequential loop with:
```python
tasks = [_count_doctors_on_page_async(curl) for curl in candidate_urls[1:4]]
for coro in asyncio.as_completed(tasks):
    result = await coro
    if result:
        return result
```

- [ ] **Step 3: Deploy and test timing**

- [ ] **Step 4: Commit**

---

### Task 6: VK followers regex — comma thousands separator

**Files:**
- Modify: `AIM/src/aim/services/lib/seo_auditor.py` lines 443-452

**Bug:** `"12,345"` parsed as `12.345` → `int(float("12.345"))` = 12.

- [ ] **Step 1: Fix comma handling**

```python
vk_str = vk_match.group(1).replace(" ", "")
if "K" in vk_str.upper():
    num = vk_str.upper().replace("K", "").replace(",", ".")
    result["vk_followers"] = int(float(num) * 1000)
else:
    result["vk_followers"] = int(vk_str.replace(",", ""))
```

- [ ] **Step 2: Deploy and test**

- [ ] **Step 3: Commit**

---

### Task 7: _is_related_entity — filter generic medical words

**Files:**
- Modify: `AIM/src/aim/services/competitor_matcher_v2.py` lines 194-199

**Bug:** Generic words (Клиника, Центр, Медицина) match → false positive filtering.

- [ ] **Step 1: Add stopword filter**

```python
_GENERIC = {"клиника", "клиник", "центр", "медицинский", "медицина",
            "институт", "группа", "компания", "общество"}
client_words = [w for w in client_name.split() if len(w) > 3 and w not in _GENERIC]
```

- [ ] **Step 2: Deploy and test**

- [ ] **Step 3: Commit**

---

### Task 8: Exhausted keys TTL in firecrawl_enricher

**Files:**
- Modify: `AIM/src/aim/services/lib/firecrawl_enricher.py` lines 30, 79-84

**Bug:** 402 keys dead forever in long-running process.

- [ ] **Step 1: Change _fc_exhausted to dict with TTL**

```python
_fc_exhausted: dict[str, float] = {}  # key → expiry timestamp
_EXHAUSTED_TTL = 3600  # 1 hour

def _mark_key_exhausted(key: str):
    with _fc_lock:
        _fc_exhausted[key] = time.time() + _EXHAUSTED_TTL

def _get_next_key():
    with _fc_lock:
        now = time.time()
        # Clear expired
        expired = [k for k, t in _fc_exhausted.items() if t < now]
        for k in expired:
            del _fc_exhausted[k]
        keys = [k for k in _load_firecrawl_keys() if k not in _fc_exhausted]
        ...
```

- [ ] **Step 2: Deploy and test**

- [ ] **Step 3: Commit**

---

## Post-Implementation

After all 8 tasks:
1. Run Code Review ×2 (code-review-skill)
2. Test on arclinic.ru (full pipeline)
3. Log errors, write fixes plan
4. Re-test arclinic.ru
5. Prepare report for Mikhail
