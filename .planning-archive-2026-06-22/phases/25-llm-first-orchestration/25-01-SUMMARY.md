---
phase: 25-llm-first-orchestration
plan: 01
status: complete
completed: 2026-06-06
---

# 25-01 SUMMARY: Instagram Doctor Verifier — Extraction Complete

## Result: SUCCESS

Skill file created and validated at `/root/.hermes/skills/software-development/presale-pipeline/social-verifier/SKILL.md` (266 lines).

## Acceptance Criteria — All Passed

| Criteria | Result |
|----------|--------|
| File exists | OK |
| YAML frontmatter (2× `---`) | OK |
| name: social-verifier | 1 match |
| Pass 1 present | 2 matches |
| Pass 2 present | 2 matches |
| Pass 3 present | 2 matches |
| Pass 4 present | 2 matches |
| Pass 5 present | 2 matches |
| RESIDENTIAL referenced | 13 matches |
| apify_keys.json referenced | 2 matches |
| Fallback to presale-pipeline | 2 matches |
| Line count >= 150 | 266 lines |
| Forbidden: water ripple | 0 |
| Forbidden: CSS | 0 |
| Forbidden: HTML-КП | 0 |
| Forbidden: GEO | 0 |
| Forbidden: ФАЗА 1 | 0 |
| Forbidden: ФАЗА 3 | 0 |
| Forbidden: Контур.Фокус | 0 |
| Forbidden: Rusprofile | 0 |

## Task 2 Validation — All Passed

| Check | Result |
|-------|--------|
| Iron rule 1 (key per pass) | 1 match |
| Iron rule 2 (don't stop after pass 1) | 1 match |
| Iron rule 3 (retroactive) | 2 matches |
| Iron rule 4 (log each pass) | 1 match |
| Iron rule 5 (mark facts) | 1 match |
| Iron rule 6 (browser+Google fallback) | 3 matches |
| Iron rule 7 (VK+TG every pass) | 1 match |
| Grade 5★ (>10K) | 1 match |
| Grade 4★ (1-10K) | 1 match |
| Grade 3★ (<1K) | 1 match |
| Grade 2★ (private) | 1 match |
| Grade 1★ (not found) | 5 matches |
| Grade 0★ (no IG) | present (as "Клиника без Instagram") |
| Input: name | 24 matches |
| Input: specialization | 4 matches |
| Input: clinic | 5 matches |
| Output: Врач | 18 matches |
| Output: Клиника | 9 matches |
| Output: IG | 16 matches |
| Output: TG | 10 matches |
| Output: VK | 8 matches |
| Output: Другие | 2 matches |
| Output: Статус | 2 matches |

## Skill Structure (8 sections)

1. YAML frontmatter (name=social-verifier, version=1.0.0)
2. When to Use (Phase 2, competitor analysis, standalone)
3. Input Specification (name, specialization, clinic — required)
4. Output Specification (master table, grades, pass-markers)
5. The 5-Pass Algorithm (verbatim from SKILL.md L306-397)
6. Iron Rules 1-7
7. Bitrix SPA Expert Extraction
8. Grade System (5★-0★)
9. Key Rotation (pass-key mapping, RESIDENTIAL proxy, rotation triggers)
10. Parallel Search (4 threads per pass)
11. Fallback Protocol (skill_view presale-pipeline)

## Benchmark Readiness

Ampermy etalon data has competitor-level social media (@wellcure.float, @respace_spa, etc.) but no individual doctor list. Full benchmark requires:
1. Running the original SKILL.md v2.55.0 on ampermy.ru to get ground truth
2. Running social-verifier skill on the same input
3. Comparing doctor discovery counts per pass

## Next: Plan 25-02

Clean up SKILL.md v2.55.0 — replace the 5-pass block (L306-397) with delegation to social-verifier skill.
