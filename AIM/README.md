# AIM Agency

**AI-first Medical Marketing Agency**

Domain: iamaim.ru

## Architecture

```
AIM/
├── src/aim/                    # Agency code
│   ├── magisters/              # SEO, Content, Ads Magisters
│   ├── subagents/              # Specialized subagents
│   └── config/                 # Configuration
├── obsidian/                   # Agent vaults (LLM Wiki pattern)
│   ├── operator/               # Operator's vault
│   ├── seo-magister/           # SEO Magister's vault
│   ├── content-magister/       # Content Magister's vault
│   └── ads-magister/           # Ads Magister's vault
├── data/                       # SQLite database
└── scripts/                    # CLI tools
```

## Hierarchy

```
Operator (Tactical Layer)
  ↓
Magisters (Domain Layer)
  ├── SEO Magister
  ├── Content Magister
  └── Ads Magister
  ↓
Subagents (Execution Layer)
  ├── Keyword Research
  ├── Content Writer
  ├── Ads Creator
  └── ...
```

## Development

All code is built from `/Users/mikhaileliseev/Desktop/Dev/!meAI` (command center).

The agency lives here in `AIM/` subdirectory.

## Framework

Uses `meai` framework from `../src/meai/`:
- Base classes: Operator, BaseMagister, BaseAgent
- Infrastructure: Event Bus, Event Store, Obsidian integration
- Core: Architect, Orchestrator, Decision Maker

## Status

✅ **Phase 2: First Real Agent Complete** (2026-05-04)

**Magisters (SKELETON - awaiting business logic):**
- ✅ SEO Magister (`src/aim/magisters/seo_magister.py`) - skeleton
- ✅ Content Magister (`src/aim/magisters/content_magister.py`) - skeleton
- ✅ Ads Magister (`src/aim/magisters/ads_magister.py`) - skeleton

**Subagents (PRODUCTION READY):**
- ✅ **Keyword Research Agent** (`src/aim/subagents/keyword_research_agent.py`) - **REAL SEO LOGIC** ⭐
  - Medical specialty detection (5 specialties)
  - Keyword expansion (4 modifier types)
  - Search volume estimation
  - Keyword difficulty scoring (0-100)
  - CPC estimation with specialty multipliers
  - Intent detection (4 types)
  - Priority scoring algorithm
  - Actionable recommendations
  - **Status: PRODUCTION READY** ✅

**Tests:**
- ✅ End-to-end test (`tests/test_end_to_end.py`) - PASSING
- ✅ Skeleton tests (`tests/test_magisters_skeleton.py`)

**What We Have:**
- ✅ Architecture validated (Operator → Magisters → Subagents)
- ✅ First real agent with business logic (Keyword Research)
- ✅ Real SEO algorithms for medical marketing
- ✅ ~500 lines of production code (no mocks!)

**Next Steps:**
1. Add more SEO Subagents (Content Optimization, Technical SEO, Link Building)
2. Add business logic to SEO Magister (coordinate subagents)
3. Create Content Subagents
4. Create Ads Subagents
5. Full integration test with real workflows

🚀 First production agent deployed!
