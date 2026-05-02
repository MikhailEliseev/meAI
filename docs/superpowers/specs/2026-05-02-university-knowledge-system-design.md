# University Knowledge System Design

**Date:** 2026-05-02  
**Author:** meAI (CEO-Architect)  
**Status:** Approved

## Overview

Design for the University knowledge system — a hierarchical learning infrastructure with Teacher (Rector), Researcher, Magisters, and vector database (Qdrant) for storing and distributing knowledge across the agency.

## Philosophy

**Deep & Correct:** Build the most complex but most functional system. Full autonomy of all components. No placeholders or "we'll finish later."

## Architecture

### High-Level Structure

```
Researcher Agent (autonomous investigator)
  ↓ (Event Bus)
Teacher Agent (rector)
  ├─ Knowledge evaluation
  ├─ Qdrant vector DB management
  └─ Distribution to Magisters
  ↓ (Event Bus)
Magisters (6 agents: SEO, Content, Ads, SMM, Analytics, Intelligence)
  ├─ Own Qdrant collections (adapted knowledge)
  └─ Obsidian vaults
  ↓
Subagents
  └─ Feedback loop through Magister → Teacher
```

### Components

#### 1. Researcher Agent

**Purpose:** Autonomous knowledge collection from multiple sources

**Inherits from:** `Agent` (base class)

**Capabilities:**
- `research_topic` — deep research via Perplexity API
- `monitor_sources` — RSS/blog/documentation monitoring
- `validate_source` — source quality validation

**Workflow:**
1. Receives request from Teacher: "Research topic X"
2. Uses Perplexity API for deep search
3. Collects information from multiple sources
4. Evaluates source quality (authority, freshness)
5. Sends findings to Teacher via Event Bus

**Database tables:**
- `researcher_tasks` — research tasks
- `researcher_sources` — information sources
- `researcher_findings` — discovered materials

**Obsidian vault:**
- `researcher/tasks/` — tasks
- `researcher/findings/` — findings
- `researcher/sources/` — sources

**Integration:**
- Perplexity API for deep research
- Web scraping (optional, fallback)
- RSS monitoring (optional)

---

#### 2. Teacher Agent

**Purpose:** Knowledge evaluation, storage, and distribution (Rector)

**Inherits from:** `Agent` (base class)

**Capabilities:**
- `evaluate_knowledge` — quality evaluation (scoring 1-10)
- `store_knowledge` — save to Qdrant
- `distribute_to_magisters` — knowledge distribution
- `search_knowledge` — Qdrant search for Magisters

**Workflow (receiving knowledge):**
1. Receives findings from Researcher
2. Evaluates quality (scoring: source, relevance, completeness)
3. Generates embeddings via `bge-m3`
4. Saves to Qdrant with metadata
5. Notifies relevant Magisters

**Workflow (Magister query):**
1. Receives question from Magister
2. Determines complexity (simple/complex/critical)
3. Searches Qdrant (vector similarity search)
4. If not found → requests Researcher
5. Sends answer to Magister

**Qdrant integration:**
- Collections: `seo_knowledge`, `content_knowledge`, `ads_knowledge`, etc.
- Metadata: `{source, date, quality_score, tags, magister_id}`
- Embeddings: `bge-m3` (768 dimensions, multilingual)

**Database tables:**
- `teacher_knowledge` — knowledge index
- `teacher_evaluations` — quality evaluations
- `teacher_distributions` — distribution history

**Fallback strategy:**
- If Qdrant unavailable → save to SQLite
- Alert Operator via Event Bus
- Sync from SQLite when Qdrant recovers

**Future scalability:**
If Teacher becomes overloaded, methods can be extracted into helper agents:
- Knowledge Curator — evaluation and storage
- Knowledge Librarian — search and retrieval
- Research Coordinator — research coordination

---

#### 3. Magisters (6 agents)

**Purpose:** Adapt knowledge for specific domains and train subagents

**List:**
1. **SEO Magister** — SEO knowledge
2. **Content Magister** — content and copywriting
3. **Ads Magister** — advertising and campaigns
4. **SMM Magister** — social media
5. **Analytics Magister** — analytics and metrics
6. **Intelligence Magister** — market intelligence

**Each Magister:**
- Inherits from `Agent` (base class)
- Has own Qdrant collection: `{direction}_magister_knowledge`
- Has own Obsidian vault: `obsidian/magisters/{direction}-magister/`

**Capabilities (common):**
- `receive_knowledge` — receive knowledge from Teacher
- `adapt_knowledge` — adapt for subagents
- `query_teacher` — query Teacher (hybrid search)
- `train_subagents` — train subagents
- `escalate_problem` — escalate problem to Teacher

**Workflow (receiving knowledge from Teacher):**
1. Receives notification from Teacher: "New knowledge on topic X"
2. Reads knowledge from message
3. Adapts for their domain (simplifies, adds examples)
4. Saves to own Qdrant collection
5. Saves to Obsidian vault
6. Notifies subagents

**Workflow (subagent query — hybrid):**
1. Receives question from subagent
2. **Simple question:** searches own Qdrant collection → answers
3. **Complex question:** queries Teacher → Teacher searches main base → answers
4. **Critical question:** Teacher requests Researcher → new research

**Question complexity determination:**
- Simple: exists in local collection (similarity > 0.8)
- Complex: not in local, but may be in main base
- Critical: nowhere, needs new research

---

### Qdrant Schema

#### Main Collections (managed by Teacher)

```python
collections = {
    "seo_knowledge": {
        "vectors": {"size": 768, "distance": "Cosine"},
        "payload_schema": {
            "content": "text",
            "source": "string",
            "quality_score": "float",  # 1-10
            "date_added": "datetime",
            "tags": "string[]",
            "researcher_id": "string",
            "language": "string"  # ru, en, etc.
        }
    },
    "content_knowledge": {...},
    "ads_knowledge": {...},
    "smm_knowledge": {...},
    "analytics_knowledge": {...},
    "intelligence_knowledge": {...}
}
```

#### Magister Collections (adapted knowledge)

```python
magister_collections = {
    "seo_magister_adapted": {
        "vectors": {"size": 768, "distance": "Cosine"},
        "payload_schema": {
            "content": "text",
            "original_id": "string",  # link to main collection
            "adapted_for": "string",  # for which subagents
            "examples": "text",  # "on fingers" examples
            "simplified": "boolean",
            "date_adapted": "datetime"
        }
    },
    # similar for other magisters
}
```

---

### Data Flows

#### Flow 1: New Knowledge (Researcher → Teacher → Magisters)

```
1. Researcher finds material
   ↓ Event: researcher.knowledge_found
2. Teacher receives, evaluates (quality_score)
   ↓ generates embeddings (bge-m3)
   ↓ saves to Qdrant (main collection)
3. Teacher determines relevant Magisters
   ↓ Event: teacher.knowledge_distributed
4. Magisters receive, adapt
   ↓ save to own collections
   ↓ save to Obsidian
```

#### Flow 2: Knowledge Query (Subagent → Magister → Teacher)

```
1. Subagent asks question to Magister
   ↓ Event: subagent.question
2. Magister searches own collection
   ↓ if similarity > 0.8 → answers immediately
   ↓ if < 0.8 → queries Teacher
3. Teacher searches main collection
   ↓ if found → answers Magister
   ↓ if not found → requests Researcher
4. Researcher investigates topic
   ↓ returns to Flow 1
```

#### Flow 3: Feedback Loop (Subagent → Magister → Teacher → Researcher)

```
1. Subagent: "Information outdated/incomplete"
   ↓ Event: subagent.feedback
2. Magister escalates to Teacher
   ↓ Event: magister.escalation
3. Teacher analyzes problem
   ↓ requests Researcher: "Update knowledge on topic X"
4. Researcher investigates → Flow 1
```

---

## Error Handling

### Qdrant Errors

**Problem:** Qdrant unavailable (Docker container crashed)

**Solution:**
- Teacher attempts reconnection (3 tries with exponential backoff)
- If failed → saves knowledge to SQLite (fallback)
- Sends alert to Operator via Event Bus
- When Qdrant recovers → syncs from SQLite

**Problem:** Collection doesn't exist

**Solution:**
- Teacher automatically creates collection on first run
- Check during `initialize()`: if no collection → create

---

### Embeddings Model Errors

**Problem:** `bge-m3` model not loaded or error

**Solution:**
- Fallback to simpler model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- If that fails → save text without vectorization, mark for reprocessing
- Alert Operator

---

### Researcher Errors

**Problem:** Perplexity API unavailable or limit exhausted

**Solution:**
- Researcher tries alternative sources (web scraping, RSS)
- If all unavailable → marks task as `failed`, escalates to Teacher
- Teacher notifies Magister: "Research failed, will retry later"

---

### Knowledge Conflicts

**Problem:** Researcher found contradictory information

**Solution:**
- Teacher saves both versions with metadata: `conflicting: true`
- Magister receives both versions, decides which to use
- Or escalates to YOU for manual decision

---

### Qdrant Overflow

**Problem:** Too much knowledge, Qdrant takes too much space

**Solution:**
- Archive old knowledge (> 1 year) to separate collection `archived_knowledge`
- Remove duplicates (similarity > 0.95)
- Remove low-quality knowledge (quality_score < 3)

---

## Technology Stack

### Vector Database
- **Qdrant** — self-hosted in Docker
- **Why:** Production-ready, scalable, full control, free
- **Deployment:** Docker container, local development

### Embeddings Model
- **Primary:** `bge-m3` (Chinese multilingual model)
- **Why:** Free, high quality, multilingual support
- **Fallback:** `paraphrase-multilingual-MiniLM-L12-v2`
- **Dimensions:** 768

### Research Integration
- **Perplexity API** — deep research
- **Web scraping** — fallback (optional)
- **RSS monitoring** — fallback (optional)

### Infrastructure
- **Event Bus** — async messaging between agents
- **SQLite** — fallback storage when Qdrant unavailable
- **Obsidian** — markdown knowledge storage
- **Docker** — Qdrant deployment

---

## Testing Strategy

### Unit Tests

**Researcher Agent:**
- Perplexity API integration
- Fallback mechanisms
- Source validation

**Teacher Agent:**
- Knowledge evaluation (quality scoring)
- Qdrant storage and retrieval
- Fallback to SQLite
- Embeddings generation

**Magister Agent:**
- Knowledge adaptation
- Hybrid search (local vs Teacher)
- Subagent training

### Integration Tests

**Full cycle:**
- Researcher → Teacher → Magister
- Subagent → Magister → Teacher → Researcher (feedback loop)

### Performance Tests

**Latency:**
- Teacher search: < 1 second
- Magister local search: < 200ms

**Throughput:**
- Teacher: 10+ concurrent requests
- Magisters: 5+ concurrent requests each

---

## Implementation Order

### Phase 1: Infrastructure
1. Qdrant Docker setup
2. Embeddings model integration (`bge-m3`)
3. Qdrant collections creation
4. SQLite fallback implementation

### Phase 2: Core Agents
1. Researcher Agent (inherits from Agent base class)
2. Teacher Agent (inherits from Agent base class)
3. Event Bus integration for both

### Phase 3: Magisters
1. Base Magister class
2. 6 Magister implementations (SEO, Content, Ads, SMM, Analytics, Intelligence)
3. Hybrid search implementation
4. Qdrant collections for each Magister

### Phase 4: Integration
1. Full data flows (3 flows)
2. Error handling
3. Feedback loops

### Phase 5: Testing
1. Unit tests
2. Integration tests
3. Performance tests
4. Load testing

---

## Success Criteria

1. ✅ Researcher autonomously collects knowledge from Perplexity API
2. ✅ Teacher evaluates and stores knowledge in Qdrant
3. ✅ Magisters receive and adapt knowledge for their domains
4. ✅ Subagents can query knowledge through Magisters (hybrid search)
5. ✅ Feedback loop works: Subagent → Magister → Teacher → Researcher
6. ✅ Error handling: Qdrant fallback to SQLite
7. ✅ Performance: Teacher search < 1s, Magister local search < 200ms
8. ✅ All tests passing

---

## Future Enhancements

### Teacher Helper Agents (if needed)
If Teacher becomes overloaded (latency > 5s, growing queue), extract methods into helper agents:
- **Knowledge Curator** — evaluation and storage
- **Knowledge Librarian** — search and retrieval
- **Research Coordinator** — research coordination

**Criteria for adding helpers:**
- Teacher processes requests > 5 seconds
- Task queue grows
- Metrics show bottleneck

### Advanced Features
- Multi-language embeddings optimization
- Knowledge graph relationships
- Automatic knowledge expiration
- Quality score learning from feedback
- Distributed Qdrant cluster (if scale requires)

---

## Notes

- This design follows "Deep & Correct" philosophy — no shortcuts, full implementation
- All agents inherit from `Agent` base class
- Event Bus for all inter-agent communication
- Qdrant as single source of truth for vector search
- SQLite as fallback for reliability
- Obsidian for human-readable knowledge storage
