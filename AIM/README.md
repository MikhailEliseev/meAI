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

✅ **Phase 1: Skeleton Complete** (2026-05-04)

**Magisters (SKELETON - no business logic):**
- ✅ SEO Magister (`src/aim/magisters/seo_magister.py`)
- ✅ Content Magister (`src/aim/magisters/content_magister.py`)
- ✅ Ads Magister (`src/aim/magisters/ads_magister.py`)

**Tests:**
- ✅ Skeleton tests (`tests/test_magisters_skeleton.py`)

**What's a Skeleton?**
- Classes inherit from BaseMagister ✅
- Methods are stubs (mock returns) ✅
- Event Bus integration ready ✅
- Obsidian vaults configured ✅
- **NO business logic yet** ⏳

**Next Steps:**
1. Run tests: `pytest tests/test_magisters_skeleton.py -v`
2. Add business logic to one Magister (start with SEO)
3. Create real Subagents
4. Integration test: Operator → Magisters → Subagents

🚧 Under construction by meAI Architect
