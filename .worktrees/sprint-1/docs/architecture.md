# Architecture Diagrams

## System Overview

```mermaid
graph TB
    User[👤 User] --> Architect[🎯 Architect<br/>Strategy Layer]
    Architect --> Operator[⚙️ Operator<br/>Tactical Layer]
    Operator --> Magisters[👥 Magisters<br/>Execution Layer]
    
    Magisters --> SEO[SEO Magister]
    Magisters --> Content[Content Magister]
    Magisters --> Ads[Ads Magister]
    Magisters --> SMM[SMM Magister]
    Magisters --> Analytics[Analytics Magister]
    Magisters --> Intelligence[Intelligence Magister]
    
    SEO --> Teacher[🎓 Teacher<br/>Knowledge Management]
    Content --> Teacher
    Ads --> Teacher
    SMM --> Teacher
    Analytics --> Teacher
    Intelligence --> Teacher
    
    Teacher --> Researcher[🔍 Researcher<br/>Knowledge Collection]
    
    Teacher --> Qdrant[(Qdrant<br/>Vector DB)]
    Researcher --> Perplexity[Perplexity API]
    Researcher --> YouTube[YouTube API]
    Researcher --> Telegram[Telegram API]
    
    style User fill:#e1f5ff
    style Architect fill:#fff4e1
    style Operator fill:#ffe1f5
    style Magisters fill:#e1ffe1
    style Teacher fill:#f5e1ff
    style Researcher fill:#ffe1e1
```

## Hybrid Search Flow

```mermaid
sequenceDiagram
    participant M as Magister
    participant LC as Local Cache<br/>(SQLite + Obsidian)
    participant T as Teacher<br/>(Qdrant)
    participant R as Researcher<br/>(APIs)
    
    M->>LC: 1. Search local cache
    alt Found in cache
        LC-->>M: Return cached results (1-5ms)
    else Not in cache
        M->>T: 2. Query Teacher
        alt Found in Qdrant
            T-->>M: Return results (50-200ms)
            M->>LC: Cache results
        else Not in Qdrant
            M->>R: 3. Request research
            R->>R: Search Perplexity/YouTube/Telegram
            R-->>T: Store findings
            T-->>M: Return results (2-10s)
            M->>LC: Cache results
        end
    end
```

## Experience Learning Flow

```mermaid
flowchart TD
    Start[Task Execution] --> Record[ExperienceTracker<br/>Record Outcome]
    Record --> Stats[Update Knowledge Stats<br/>success_rate, avg_score]
    
    Stats --> Quality{Enough Data?<br/>min 5 uses}
    Quality -->|Yes| Calculate[QualityUpdater<br/>Calculate New Score]
    Quality -->|No| Wait[Wait for more data]
    
    Calculate --> Update[Update Teacher<br/>Qdrant Metadata]
    Update --> Check{Should Deprecate?}
    
    Check -->|Quality < 3.0| Deprecate[DeprecationManager<br/>Mark as Deprecated]
    Check -->|Success < 30%| Deprecate
    Check -->|Avg Score < 0.4| Deprecate
    Check -->|OK| Keep[Keep Active]
    
    Deprecate --> Exclude[Exclude from Search]
    Keep --> Analytics[LearningAnalytics<br/>Generate Insights]
    
    Analytics --> Health[System Health Score]
    Analytics --> Performance[Performance Reports]
    Analytics --> Trends[Learning Trends]
    
    style Record fill:#e1f5ff
    style Calculate fill:#fff4e1
    style Deprecate fill:#ffe1e1
    style Analytics fill:#e1ffe1
```

## Quality Score Calculation

```mermaid
graph LR
    A[Experience Data] --> B[Success Rate<br/>0.0 - 1.0]
    A --> C[Average Score<br/>0.0 - 1.0]
    
    B --> D[Target from Success<br/>1.0 + success * 9.0]
    C --> E[Target from Score<br/>1.0 + avg * 9.0]
    
    D --> F[Weighted Average<br/>60% success + 40% score]
    E --> F
    
    F --> G[Apply Learning Rate<br/>adjustment * 0.3]
    G --> H[New Quality Score<br/>1.0 - 10.0]
    
    style A fill:#e1f5ff
    style F fill:#fff4e1
    style H fill:#e1ffe1
```

## Database Schema

```mermaid
erDiagram
    EXPERIENCES ||--o{ KNOWLEDGE_STATS : updates
    EXPERIENCES {
        string id PK
        string magister_id
        string task_id
        json knowledge_ids
        string outcome
        float outcome_score
        text feedback
        timestamp created_at
    }
    
    KNOWLEDGE_STATS {
        string knowledge_id PK
        int total_uses
        int successful_uses
        int failed_uses
        float total_score
        timestamp last_used_at
        timestamp updated_at
    }
    
    QUALITY_UPDATES {
        string id PK
        string knowledge_id FK
        float old_score
        float new_score
        float adjustment
        float success_rate
        float average_score
        int usage_count
        text reason
        timestamp updated_at
    }
    
    DEPRECATIONS {
        string id PK
        string knowledge_id FK
        text reason
        float quality_at_deprecation
        float success_rate_at_deprecation
        int usage_count_at_deprecation
        timestamp deprecated_at
        string deprecated_by
        boolean active
        timestamp undeprecated_at
        text undeprecation_reason
    }
    
    MAGISTER_KNOWLEDGE_CACHE {
        string id PK
        string magister_id
        string knowledge_id
        text content
        json metadata
        timestamp cached_at
        timestamp expires_at
    }
    
    KNOWLEDGE_STATS ||--o{ QUALITY_UPDATES : tracks
    KNOWLEDGE_STATS ||--o{ DEPRECATIONS : triggers
```

## Component Interaction

```mermaid
graph TB
    subgraph "Execution Layer"
        M1[SEO Magister]
        M2[Content Magister]
        M3[Ads Magister]
        M4[SMM Magister]
        M5[Analytics Magister]
        M6[Intelligence Magister]
    end
    
    subgraph "Knowledge Layer"
        T[Teacher Agent]
        R[Researcher Agent]
        Q[(Qdrant)]
    end
    
    subgraph "Learning Layer"
        ET[ExperienceTracker]
        QU[QualityUpdater]
        DM[DeprecationManager]
        LA[LearningAnalytics]
    end
    
    subgraph "Storage Layer"
        DB[(PostgreSQL)]
        OV[Obsidian Vaults]
    end
    
    M1 --> T
    M2 --> T
    M3 --> T
    M4 --> T
    M5 --> T
    M6 --> T
    
    T --> Q
    T --> R
    
    M1 --> ET
    M2 --> ET
    M3 --> ET
    M4 --> ET
    M5 --> ET
    M6 --> ET
    
    ET --> QU
    QU --> DM
    DM --> LA
    
    ET --> DB
    QU --> DB
    DM --> DB
    
    M1 --> OV
    M2 --> OV
    M3 --> OV
    M4 --> OV
    M5 --> OV
    M6 --> OV
    
    T --> DB
    Q --> DB
    
    style T fill:#f5e1ff
    style R fill:#ffe1e1
    style ET fill:#e1f5ff
    style QU fill:#fff4e1
    style DM fill:#ffe1e1
    style LA fill:#e1ffe1
```

## Event Flow

```mermaid
sequenceDiagram
    participant M as Magister
    participant EB as Event Bus
    participant T as Teacher
    participant R as Researcher
    participant ET as ExperienceTracker
    
    Note over M,ET: Task Execution
    M->>M: Execute task
    M->>ET: Record experience
    
    Note over M,T: Knowledge Search
    M->>EB: Publish magister.query
    EB->>T: Deliver event
    T->>T: Search Qdrant
    
    alt Found in Qdrant
        T->>EB: Publish knowledge.found
        EB->>M: Deliver results
    else Not found
        T->>EB: Publish research.requested
        EB->>R: Deliver request
        R->>R: Search external sources
        R->>T: Store findings
        T->>EB: Publish knowledge.distributed
        EB->>M: Deliver results
    end
    
    Note over M,ET: Learning Cycle
    ET->>ET: Update stats
    ET->>EB: Publish experience.recorded
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/Traefik]
    end
    
    subgraph "Application Tier"
        A1[FastAPI Instance 1]
        A2[FastAPI Instance 2]
        A3[FastAPI Instance 3]
    end
    
    subgraph "Data Tier"
        PG[(PostgreSQL<br/>Primary)]
        PGR[(PostgreSQL<br/>Replica)]
        Q[(Qdrant)]
        RD[(Redis Cache)]
    end
    
    subgraph "Storage"
        OV[Obsidian Vaults]
        BK[Backups]
    end
    
    subgraph "Monitoring"
        PR[Prometheus]
        GR[Grafana]
        LK[Loki Logs]
    end
    
    LB --> A1
    LB --> A2
    LB --> A3
    
    A1 --> PG
    A2 --> PG
    A3 --> PG
    
    A1 --> Q
    A2 --> Q
    A3 --> Q
    
    A1 --> RD
    A2 --> RD
    A3 --> RD
    
    PG --> PGR
    
    A1 --> OV
    A2 --> OV
    A3 --> OV
    
    PG --> BK
    Q --> BK
    OV --> BK
    
    A1 --> PR
    A2 --> PR
    A3 --> PR
    
    PR --> GR
    A1 --> LK
    A2 --> LK
    A3 --> LK
    
    style LB fill:#e1f5ff
    style PG fill:#fff4e1
    style Q fill:#ffe1f5
    style RD fill:#e1ffe1
```

## Data Flow

```mermaid
flowchart LR
    subgraph Input
        U[User Request]
    end
    
    subgraph Processing
        O[Operator]
        M[Magister]
        T[Teacher]
        R[Researcher]
    end
    
    subgraph Storage
        LC[Local Cache]
        QD[(Qdrant)]
        DB[(PostgreSQL)]
    end
    
    subgraph Learning
        ET[Experience<br/>Tracker]
        QU[Quality<br/>Updater]
    end
    
    U --> O
    O --> M
    M --> LC
    LC -.->|Cache miss| T
    T --> QD
    QD -.->|Not found| R
    R --> T
    T --> M
    M --> U
    
    M --> ET
    ET --> DB
    ET --> QU
    QU --> T
    
    style U fill:#e1f5ff
    style M fill:#e1ffe1
    style T fill:#f5e1ff
    style R fill:#ffe1e1
    style ET fill:#fff4e1
```

## Performance Metrics

```mermaid
graph LR
    subgraph "Search Performance"
        L1[Local Cache<br/>1-5ms<br/>80-90% hit rate]
        L2[Teacher Query<br/>50-200ms<br/>Qdrant search]
        L3[Researcher<br/>2-10s<br/>External APIs]
    end
    
    subgraph "Learning Performance"
        E1[Record Experience<br/>5-10ms<br/>SQLite insert]
        E2[Update Quality<br/>10-20ms<br/>Calculate + log]
        E3[Scan Deprecation<br/>100-200ms<br/>100 items]
    end
    
    subgraph "Analytics Performance"
        A1[System Health<br/>50-100ms<br/>Aggregation]
        A2[Knowledge Report<br/>20-50ms<br/>Single query]
        A3[Trends<br/>100-200ms<br/>7 days]
    end
    
    style L1 fill:#e1ffe1
    style L2 fill:#fff4e1
    style L3 fill:#ffe1e1
    style E1 fill:#e1f5ff
    style E2 fill:#fff4e1
    style E3 fill:#ffe1f5
```

## See Also

- [Getting Started](getting-started.md)
- [Magisters Guide](magisters.md)
- [Experience Learning](experience-learning.md)
- [Deployment Guide](deployment.md)
