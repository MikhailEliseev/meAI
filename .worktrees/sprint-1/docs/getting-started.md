# Getting Started with meAI

## Introduction

Этот гайд поможет вам быстро начать работу с meAI - системой для создания AI-first medical marketing agency.

## Prerequisites

Перед началом убедитесь, что у вас установлено:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker** - [Download](https://www.docker.com/get-started)
- **Git** - [Download](https://git-scm.com/downloads)
- **Obsidian** (опционально) - [Download](https://obsidian.md/)

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd meAI
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup Qdrant

```bash
# Start Qdrant with Docker
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Verify Qdrant is running
curl http://localhost:6333/
```

### Step 5: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**.env example:**
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/meai.db

# Qdrant
QDRANT_URL=http://localhost:6333

# Obsidian
OBSIDIAN_VAULT_PATH=./obsidian

# API Keys (optional for now)
PERPLEXITY_API_KEY=your-key-here
YOUTUBE_API_KEY=your-key-here
TELEGRAM_BOT_TOKEN=your-token-here

# Logging
LOG_LEVEL=INFO
```

### Step 6: Initialize System

```bash
# Create data directory
mkdir -p data

# Initialize Magisters
python scripts/setup_magisters.py
```

**Expected output:**
```
🔧 Setting up Magister Agents

✅ Event Bus initialized

📋 Setting up 6 Magisters...

✅ SEO Magister initialized
   Vault: ./obsidian/seo-magister
   Domain: seo
   Capabilities: 9

✅ Content Magister initialized
   ...

=== Setup Complete ===

✅ Successfully set up: 6 Magisters
```

## Quick Start Examples

### Example 1: Search Knowledge with SEO Magister

```python
import asyncio
from pathlib import Path
from meai.agents.magisters import SEOMagister
from meai.events.event_bus import EventBus

async def main():
    # Initialize
    event_bus = EventBus()
    seo = SEOMagister(
        event_bus=event_bus,
        vault_path=Path("./obsidian/seo-magister"),
    )
    await seo.initialize()
    
    # Search knowledge
    results = await seo.search_knowledge(
        query="SEO best practices for medical websites",
        search_local=True,
        search_teacher=False,  # Teacher not set up yet
    )
    
    print(f"Found {len(results)} results")
    for result in results:
        print(f"- {result['content'][:100]}...")
    
    await seo.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:**
```bash
python examples/search_knowledge.py
```

### Example 2: Record Experience and Update Quality

```python
import asyncio
from meai.learning import ExperienceTracker, QualityUpdater

async def main():
    # Initialize
    tracker = ExperienceTracker()
    await tracker.initialize()
    
    updater = QualityUpdater(experience_tracker=tracker)
    await updater.initialize()
    
    # Record 10 successful experiences
    for i in range(10):
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-test"],
            outcome="success",
            outcome_score=0.9,
        )
    
    # Get stats
    stats = await tracker.get_knowledge_stats("knowledge-test")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Average score: {stats['average_score']:.2f}")
    
    # Update quality
    result = await updater.update_knowledge_quality(
        knowledge_id="knowledge-test",
        current_score=7.0,
    )
    
    print(f"Quality: {result['old_score']} → {result['new_score']}")
    print(f"Reason: {result['reason']}")
    
    await tracker.shutdown()
    await updater.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:**
```bash
python examples/experience_learning.py
```

### Example 3: Execute Task with Magister

```python
import asyncio
from meai.agents.magisters import SEOMagister
from meai.agents.base_agent import Task
from meai.events.event_bus import EventBus

async def main():
    # Initialize
    event_bus = EventBus()
    seo = SEOMagister(event_bus=event_bus)
    await seo.initialize()
    
    # Create task
    task = Task(
        task_id="task-1",
        description="Analyze keywords for medical SEO campaign",
        metadata={
            "capability": "analyze_keywords",
            "keywords": [
                "medical SEO",
                "healthcare marketing",
                "patient acquisition",
            ],
        }
    )
    
    # Execute task
    result = await seo.execute_task(task)
    
    print(f"Status: {result.status}")
    print(f"Keywords analyzed: {result.result['keywords_analyzed']}")
    
    await seo.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

**Run:**
```bash
python examples/execute_task.py
```

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/learning/test_experience_tracker.py

# Run with verbose output
pytest tests/unit/ -v
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration test
pytest tests/integration/test_experience_learning_flow.py
```

### End-to-End Tests

```bash
# Test Magisters system
python scripts/test_magisters_core.py

# Test Experience Learning
python scripts/test_experience_learning.py
```

**Expected output:**
```
🧪 Testing Experience Learning System
   Time: 2026-05-02 19:17:10

=== TEST: Initialize Experience Learning System ===
✅ ExperienceTracker initialized
✅ QualityUpdater initialized
✅ DeprecationManager initialized
✅ LearningAnalytics initialized

=== TEST: Record Task Experiences ===
✅ Recorded 30 excellent experiences
✅ Recorded 30 average experiences
✅ Recorded 30 poor experiences

...

🎉 ALL TESTS PASSED!
```

## Project Structure

```
meAI/
├── src/meai/              # Source code
│   ├── agents/            # Magisters and base agents
│   ├── learning/          # Experience learning system
│   ├── knowledge/         # Qdrant, embeddings, fallback
│   ├── integrations/      # Perplexity, YouTube, Telegram
│   ├── events/            # Event Bus and Event Store
│   ├── storage/           # Database
│   └── memory/            # Obsidian integration
│
├── tests/                 # Tests
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
│
├── scripts/               # Utility scripts
│   ├── setup_magisters.py
│   ├── test_magisters_core.py
│   └── test_experience_learning.py
│
├── obsidian/              # Obsidian vaults
│   ├── seo-magister/
│   ├── content-magister/
│   └── ...
│
├── data/                  # SQLite databases
│   └── meai.db
│
├── docs/                  # Documentation
│   ├── magisters.md
│   ├── experience-learning.md
│   └── ...
│
├── CLAUDE.md              # Project instructions
├── README.md              # Main readme
└── requirements.txt       # Dependencies
```

## Next Steps

### 1. Explore Magisters

```bash
# Read Magisters documentation
cat docs/magisters.md

# Try different Magisters
python examples/content_magister.py
python examples/ads_magister.py
```

### 2. Setup Teacher Agent

```bash
# Initialize Teacher with Qdrant
python scripts/setup_teacher.py

# Test Teacher-Magister integration
python scripts/test_teacher_integration.py
```

### 3. Setup Researcher Agent

```bash
# Configure API keys in .env
nano .env

# Initialize Researcher
python scripts/setup_researcher.py

# Test full knowledge flow
python scripts/test_knowledge_flow.py
```

### 4. Explore Experience Learning

```bash
# Read Experience Learning docs
cat docs/experience-learning.md

# Run analytics examples
python examples/learning_analytics.py
```

### 5. View Obsidian Vaults

```bash
# Open Obsidian
# File → Open Vault → Select ./obsidian/seo-magister

# Explore:
# - knowledge/ - Cached knowledge
# - tasks/ - Task execution logs
# - decisions/ - Decision records
```

## Common Tasks

### Add New Magister

```python
# Create custom_magister.py
from meai.agents.magisters import BaseMagister
from meai.agents.base_agent import Task, TaskResult

class CustomMagister(BaseMagister):
    def __init__(self, **kwargs):
        super().__init__(
            agent_id="custom-magister-1",
            magister_type="custom",
            domain="custom_domain",
            **kwargs
        )
    
    def get_capabilities(self) -> list[str]:
        base = super().get_capabilities()
        return base + ["custom_capability"]
    
    async def execute_task(self, task: Task) -> TaskResult:
        capability = task.metadata.get("capability")
        
        if capability == "custom_capability":
            return await self._handle_custom(task)
        else:
            return await super().execute_task(task)
    
    async def _handle_custom(self, task: Task) -> TaskResult:
        # Your logic here
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={"custom": "result"},
        )
```

### Clear Cache

```bash
# Clear SQLite cache
rm data/meai.db
python scripts/setup_magisters.py

# Clear Obsidian vaults
rm -rf obsidian/*/knowledge/*
```

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Check System Health

```python
from meai.learning import LearningAnalytics

analytics = LearningAnalytics(tracker, updater, deprecation)
health = await analytics.get_system_health()

print(f"Health Score: {health['health_score']}/10")
```

## Troubleshooting

### Qdrant not running

```bash
# Check if Qdrant is running
curl http://localhost:6333/

# Restart Qdrant
docker restart <qdrant-container-id>

# Check logs
docker logs <qdrant-container-id>
```

### Import errors

```bash
# Verify venv is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

### Database locked

```bash
# Close all connections
# Delete database
rm data/meai.db

# Reinitialize
python scripts/setup_magisters.py
```

### Tests failing

```bash
# Run with verbose output
pytest tests/ -v -s

# Run specific test
pytest tests/unit/learning/test_experience_tracker.py::test_record_experience -v
```

## Resources

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Tests**: [tests/](tests/)
- **Scripts**: [scripts/](scripts/)

## Getting Help

1. Check [documentation](docs/)
2. Run tests to verify setup
3. Check logs in `data/logs/`
4. Review CLAUDE.md for project context

## What's Next?

- [Magisters Documentation](magisters.md)
- [Experience Learning](experience-learning.md)
- [API Reference](api-reference.md)
- [Deployment Guide](deployment.md)

---

**Ready to build your AI-first medical marketing agency!** 🚀
