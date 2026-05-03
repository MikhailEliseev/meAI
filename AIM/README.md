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

🚧 Under construction by meAI Architect
