# Research Part 4: Knowledge Base & Documentation Systems

**Date:** 2026-05-15  
**Focus:** GitHub repos analysis + documentation architecture patterns  
**Budget:** N/A (GitHub search + code analysis)

---

## Executive Summary

Исследовал 3 production-ready репозитория и 10+ статей о документационных системах. Нашёл паттерны для:
- Client-side search (FlexSearch) vs Semantic search (pgvector + OpenAI embeddings)
- MDX processing pipeline (next-mdx-remote + rehype/remark plugins)
- Content indexing strategies (build-time vs runtime)
- Navigation architecture (hierarchical + hub-and-spoke + clusters)

**Ключевой инсайт:** Современные knowledge base системы используют **hybrid search** (semantic + full-text) с **build-time indexing** для скорости и **MDX** для интерактивности.

---

## Top 3 GitHub Repositories

### 1. docs-generator (rabinarayanpatra) ⭐ Best for Client-Side Search

**URL:** https://github.com/rabinarayanpatra/docs-generator  
**Stars:** ~50+ (новый, но качественный)  
**Stack:** Next.js 16, TypeScript, FlexSearch, MDX  

**Архитектурные паттерны:**

1. **FlexSearch Index (Client-Side)**
   - Build-time indexing всех MDX файлов
   - Preset: 'match', tokenize: 'forward', cache: true
   - Индексирует: title (highest weight) → description → headings → content
   - Snippet extraction с context (50 chars before, 100 after match)

```typescript
// src/lib/search.ts
const searchIndex = new Index({
  preset: 'match',
  tokenize: 'forward',
  cache: true,
})

// Index multiple fields with different weights
searchIndex.add(id, doc.frontmatter.title)      // Highest priority
searchIndex.add(id, doc.frontmatter.description)
headings.forEach(h => searchIndex.add(id, h))
searchIndex.add(id, plainContent)               // Lowest priority
```

2. **Markdown Stripping для Search**
   - Удаляет frontmatter, code blocks, inline code, images, links
   - Сохраняет только plain text для индексации
   - Извлекает headings отдельно для приоритетного поиска

```typescript
function stripMarkdown(markdown: string): string {
  return markdown
    .replace(/^---[\s\S]*?---/, '')           // Remove frontmatter
    .replace(/```[\s\S]*?```/g, '')           // Remove code blocks
    .replace(/`[^`]+`/g, '')                  // Remove inline code
    .replace(/!\[.*?\]\(.*?\)/g, '')          // Remove images
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Keep link text only
    .replace(/^#{1,6}\s+/gm, '')              // Remove heading markers
    .replace(/\s+/g, ' ')
    .trim()
}
```

3. **Search Dialog с Keyboard Navigation**
   - Cmd+K / Ctrl+K для открытия
   - Arrow keys для навигации
   - Enter для перехода
   - Debounce 300ms для оптимизации
   - Highlight matched text в результатах

4. **MDX Processing Pipeline**
   - next-mdx-remote для SSR
   - rehype-pretty-code для syntax highlighting (dual theme: github-dark/light)
   - rehype-katex для math формул
   - rehype-slug + rehype-autolink-headings для anchor links
   - remarkGfm для GitHub Flavored Markdown

**Что взять:**
- ✅ FlexSearch setup с multi-field indexing
- ✅ Markdown stripping функция
- ✅ Search dialog component с keyboard shortcuts
- ✅ Snippet extraction логика
- ✅ MDX processing pipeline (rehype/remark plugins)

---

### 2. docs.dblayer.dev (scorcism) ⭐ Best for Build-Time Indexing

**URL:** https://github.com/scorcism/docs.dblayer.dev  
**Stack:** Next.js 15, TypeScript, MDX, Custom Search Index  

**Архитектурные паттерны:**

1. **Build-Time Search Index Generation**
   - Script `scripts/content.ts` генерирует `public/search-data/documents.json`
   - Запускается при build: `"postbuild": "tsx scripts/content.ts"`
   - Индекс загружается на клиенте для instant search

```typescript
// scripts/content.ts
async function convertMdxToJson() {
  const mdxFiles = await getMdxFiles(docsDir)
  const combinedData = []

  for (const file of mdxFiles) {
    const jsonData = await processMdxFile(file)
    combinedData.push(jsonData)
  }

  await fs.writeFile(
    path.join(outputDir, 'documents.json'),
    JSON.stringify(combinedData, null, 2)
  )
}
```

2. **Advanced Content Cleaning**
   - Удаляет custom MDX components (Tabs, Card, Mermaid, etc.)
   - Извлекает keywords из frontmatter + headings + bold text + inline code
   - Создаёт `_searchMeta` с cleanContent, headings, keywords

```typescript
function cleanContentForSearch(content: string): string {
  let cleaned = content
    .replace(/```[\s\S]*?```/g, ' ')                    // Code blocks
    .replace(/`([^`]+)`/g, '$1')                        // Inline code
    .replace(/#{1,6}\s+(.+)/g, '$1')                    // Headings
    .replace(/\*\*(.+?)\*\*/g, '$1')                    // Bold
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')           // Links
    .replace(/[^\w\s-:]/g, ' ')                         // Special chars
    .replace(/\s+/g, ' ')
    .toLowerCase()
    .trim()
  
  return cleaned
}
```

3. **Custom MDX Components Removal**
   - unified + remark-mdx для парсинга
   - visit() для удаления custom components из AST
   - Сохраняет только стандартный Markdown для search

```typescript
function removeCustomComponents() {
  const customComponentNames = [
    'Tabs', 'TabsList', 'TabsTrigger', 'pre', 'Mermaid',
    'Card', 'CardGrid', 'Step', 'StepItem', 'Note',
    'FileTree', 'Folder', 'File'
  ]

  return (tree: Node) => {
    visit(tree, 'mdxJsxFlowElement', (node, index, parent) => {
      if (customComponentNames.includes(node.name)) {
        parent.children.splice(index, 1)
      }
    })
  }
}
```

4. **Keyword Extraction Strategy**
   - Frontmatter keywords (manual)
   - H2 headings (auto)
   - Bold text (auto)
   - Inline code (auto)
   - Deduplicate с Set

**Что взять:**
- ✅ Build-time indexing script
- ✅ Advanced content cleaning функция
- ✅ Custom components removal (для MDX)
- ✅ Keyword extraction strategy
- ✅ _searchMeta pattern для metadata

---

### 3. commonbase (your-commonbase) ⭐ Best for Semantic Search

**URL:** https://github.com/your-commonbase/commonbase  
**Stars:** 15  
**Stack:** Next.js 15, PostgreSQL + pgvector, OpenAI embeddings, Drizzle ORM  

**Архитектурные паттерны:**

1. **Hybrid Search (Semantic + Full-Text)**
   - Semantic search: OpenAI embeddings + pgvector cosine similarity
   - Full-text search: PostgreSQL FTS (to_tsvector + plainto_tsquery)
   - Smart deduplication: semantic results > FTS results

```typescript
// src/app/api/search/route.ts
export async function POST(request: NextRequest) {
  const results = []

  // 1. Semantic search
  const queryEmbedding = await generateEmbedding(query)
  const vectorString = `[${queryEmbedding.join(',')}]`
  
  const semanticResults = await db
    .select({
      id: commonbase.id,
      similarity: sql`1 - (${embeddings.embedding} <=> ${vectorString}::vector)`,
    })
    .where(sql`1 - (${embeddings.embedding} <=> ${vectorString}::vector) > ${threshold}`)
    .orderBy(sql`${embeddings.embedding} <=> ${vectorString}::vector`)
    .limit(limit)

  // 2. Full-text search
  const ftsResults = await db
    .select({ id: commonbase.id })
    .where(sql`to_tsvector('english', ${commonbase.data}) @@ plainto_tsquery('english', ${query})`)
    .orderBy(sql`ts_rank(to_tsvector('english', ${commonbase.data}), plainto_tsquery('english', ${query})) DESC`)
    .limit(limit)

  // 3. Deduplicate (semantic first, then FTS)
  return deduplicatedResults
}
```

2. **OpenAI Embeddings Generation**
   - Model: text-embedding-3-small
   - Dimensions: 1536
   - Timeout: 8000ms (prevent hanging)
   - Error handling: continue with FTS if embedding fails

```typescript
// src/lib/embeddings.ts
export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'text-embedding-3-small',
      input: text,
      dimensions: 1536,
    }),
  })

  const data = await response.json()
  return data.data[0].embedding
}
```

3. **pgvector Schema**
   - Custom vector type для Drizzle ORM
   - Separate embeddings table (1:1 с commonbase)
   - Cascade delete для referential integrity

```typescript
// src/lib/db/schema.ts
const vector = customType<{ data: number[] }>({
  dataType() {
    return 'vector(1536)'
  },
  toDriver(value: number[]): string {
    return `[${value.join(',')}]`
  },
  fromDriver(value: string): number[] {
    return value.slice(1, -1).split(',').map(Number)
  },
})

export const commonbase = pgTable('commonbase', {
  id: uuid('id').primaryKey(),
  data: text('data').notNull(),
  metadata: json('metadata'),
})

export const embeddings = pgTable('embeddings', {
  id: uuid('id').primaryKey().references(() => commonbase.id, { onDelete: 'cascade' }),
  embedding: vector('embedding').notNull(),
})
```

4. **Cosine Similarity Search**
   - Operator: `<=>` (cosine distance)
   - Similarity: `1 - distance` (convert to similarity score)
   - Threshold: 0.5-0.7 (configurable)
   - Order by distance (ascending = most similar first)

**Что взять:**
- ✅ Hybrid search pattern (semantic + FTS)
- ✅ OpenAI embeddings integration
- ✅ pgvector schema setup
- ✅ Deduplication strategy
- ✅ Timeout handling для embeddings

---

## Documentation Architecture Patterns

### 1. Information Architecture (IA)

**Три основных паттерна:**

1. **Hierarchical (Tree Structure)**
   - Категории → Подкатегории → Страницы
   - Лучше для: API docs, reference documentation
   - Пример: `/api/users/create`, `/api/users/update`

2. **Hub-and-Spoke**
   - Центральная landing page → связанные страницы
   - Лучше для: feature documentation, guides
   - Пример: "Authentication Hub" → OAuth, JWT, API Keys, SSO

3. **Topic Clusters**
   - Pillar page → cluster pages (связанные темы)
   - Лучше для: conceptual documentation, tutorials
   - Пример: "SEO Guide" → keyword research, on-page, technical SEO

**Best Practice:** Комбинировать все три паттерна в зависимости от типа контента.

### 2. Folder Structure (Recommended)

```
docs/
├── index.md                    # Landing page
├── getting-started/
│   ├── installation.md
│   ├── quickstart.md
│   └── first-project.md
├── guides/                     # How-to (Hub-and-Spoke)
│   ├── authentication.md
│   ├── deploying.md
│   └── migrating.md
├── reference/                  # API reference (Hierarchical)
│   ├── api/
│   │   ├── users.md
│   │   └── projects.md
│   ├── cli.md
│   └── configuration.md
├── concepts/                   # Explanation (Topic Clusters)
│   ├── architecture.md
│   └── data-model.md
└── assets/
    └── images/
```

**Правила:**
- Flat is better than deep (max 2-3 levels)
- Name files by topic, not type (`authentication.md`, not `guide-auth.md`)
- One concept per file (searchability)
- Landing page per section (`index.md`)

### 3. Navigation Patterns

**Three-Layer Architecture:**

1. **Dimensions** (optional): product, version, language
2. **Views**: tabs, dropdowns (how content is arranged)
3. **Content**: groups, pages, API sections

**Example:**
```
Version (dimension) → Guides (tab) → Authentication (group) → OAuth (page)
```

**Best Practices:**
- Use tabs for big, mutually exclusive areas (Guides vs API)
- Use dropdowns for modes/profiles (Cloud vs Self-hosted)
- Keep structure stable (links don't break)
- Mirror structure across versions/languages

### 4. Search Optimization

**Three strategies:**

1. **Client-Side Search (FlexSearch)**
   - Pros: Instant, no backend, works offline
   - Cons: Index size (limit ~10MB), no semantic search
   - Best for: Small-medium docs (<1000 pages)

2. **Server-Side Search (MeiliSearch, Algolia)**
   - Pros: Unlimited size, typo tolerance, faceted search
   - Cons: Infrastructure cost, latency
   - Best for: Large docs (>1000 pages)

3. **Hybrid Search (Semantic + FTS)**
   - Pros: Best relevance, handles natural language
   - Cons: OpenAI API cost, complexity
   - Best for: Knowledge bases with complex queries

**Recommendation для AIM:**
- Start: FlexSearch (client-side, simple)
- Scale: MeiliSearch (self-hosted, fast)
- Future: Hybrid (semantic search для AI-powered queries)

---

## Tools & Libraries

### MDX Processing

```json
{
  "next-mdx-remote": "^5.0.0",        // SSR MDX compilation
  "gray-matter": "^4.0.3",            // Frontmatter parsing
  "remark-gfm": "^4.0.0",             // GitHub Flavored Markdown
  "remark-math": "^6.0.0",            // Math support
  "rehype-slug": "^6.0.0",            // Auto heading IDs
  "rehype-autolink-headings": "^7.0.0", // Anchor links
  "rehype-pretty-code": "^0.13.0",    // Syntax highlighting
  "rehype-katex": "^7.0.0",           // Math rendering
  "unist-util-visit": "^5.0.0"        // AST traversal
}
```

### Search

```json
{
  "flexsearch": "^0.8.212",           // Client-side search
  "meilisearch": "^0.41.0",           // Server-side search (alternative)
  "openai": "^5.20.1",                // Embeddings для semantic search
  "pgvector": "^0.2.0"                // Vector similarity (PostgreSQL)
}
```

### UI Components

```json
{
  "@radix-ui/react-dialog": "^1.1.15",     // Search modal
  "@radix-ui/react-tabs": "^1.1.13",       // Navigation tabs
  "@radix-ui/react-dropdown-menu": "^2.1.16", // Dropdowns
  "lucide-react": "^0.554.0",              // Icons
  "cmdk": "^1.1.1",                        // Command palette (alternative)
  "framer-motion": "^12.23.24"             // Animations
}
```

### Diagramming

```json
{
  "mermaid": "^11.12.1",              // Flowcharts, sequence diagrams
  "katex": "^0.16.25"                 // Math formulas
}
```

---

## Implementation Recommendations

### Phase 1: Basic Knowledge Base (Week 1-2)

**Goal:** Markdown-based docs с client-side search

**Stack:**
- Next.js 15 App Router
- MDX (next-mdx-remote)
- FlexSearch (client-side)
- Tailwind CSS + Radix UI

**Features:**
- Hierarchical folder structure (`docs/`)
- MDX processing pipeline (rehype/remark)
- FlexSearch index (build-time generation)
- Search dialog (Cmd+K)
- Syntax highlighting (rehype-pretty-code)
- Dark mode (next-themes)

**Files to create:**
```
AIM/knowledge-base/
├── app/
│   ├── docs/[...slug]/page.tsx     # Dynamic doc pages
│   └── api/search/route.ts         # Search API
├── lib/
│   ├── mdx.ts                      # MDX compilation
│   ├── search.ts                   # FlexSearch setup
│   └── docs.ts                     # Doc file reading
├── components/
│   ├── search-dialog.tsx           # Search UI
│   └── mdx-components.tsx          # Custom MDX components
└── content/
    └── docs/                       # Markdown files
```

**Estimated time:** 1-2 weeks (1 developer)

### Phase 2: Advanced Features (Week 3-4)

**Goal:** Versioning, analytics, AI assistant

**Features:**
- Documentation versioning (v1, v2, etc.)
- Analytics (page views, search queries)
- AI assistant (RAG с OpenAI)
- Contribution workflow (GitHub PR)
- Link checker (broken links detection)

**Stack additions:**
- Vercel Analytics
- OpenAI API (embeddings + chat)
- GitHub API (PR creation)

**Estimated time:** 1-2 weeks (1 developer)

### Phase 3: Semantic Search (Week 5-6)

**Goal:** Hybrid search (semantic + FTS)

**Features:**
- PostgreSQL + pgvector
- OpenAI embeddings generation
- Hybrid search API
- Deduplication strategy
- Search analytics

**Stack additions:**
- PostgreSQL (Supabase or self-hosted)
- pgvector extension
- Drizzle ORM

**Estimated time:** 1-2 weeks (1 developer)

---

## Cost Analysis

### Client-Side Search (FlexSearch)

**Costs:**
- Infrastructure: $0 (static hosting)
- Search: $0 (client-side)
- Total: **$0/month**

**Limitations:**
- Index size: ~10MB max (compressed)
- Pages: ~1000 max
- No semantic search

### Server-Side Search (MeiliSearch)

**Costs:**
- Infrastructure: $25-50/month (VPS)
- Search: $0 (self-hosted)
- Total: **$25-50/month**

**Benefits:**
- Unlimited pages
- Typo tolerance
- Faceted search
- Fast (<50ms)

### Hybrid Search (Semantic + FTS)

**Costs:**
- Infrastructure: $25-50/month (PostgreSQL + pgvector)
- OpenAI embeddings: $0.0001/1K tokens
  - 1000 pages × 500 tokens = 500K tokens = **$0.05 one-time**
  - Search queries: 100/day × 50 tokens = 5K tokens/day = **$0.15/month**
- Total: **$25-50/month + $0.15/month = $25-50/month**

**Benefits:**
- Best relevance
- Natural language queries
- Semantic similarity
- Future-proof (AI-powered)

**Recommendation:** Start с FlexSearch ($0), migrate к MeiliSearch при росте (>1000 pages), добавить semantic search для AI assistant.

---

## Key Learnings

### 1. Build-Time Indexing > Runtime Indexing

**Почему:**
- Faster search (no DB queries)
- Lower infrastructure cost
- Works offline
- Better for static content

**Когда использовать runtime:**
- Dynamic content (user-generated)
- Real-time updates required
- Content too large for client

### 2. Hybrid Search = Best UX

**Semantic search:**
- Handles natural language ("how to deploy?")
- Finds related content (even without exact keywords)
- Better for AI assistants

**Full-text search:**
- Exact matches (API names, error codes)
- Faster (no embedding generation)
- Fallback when semantic fails

**Deduplication strategy:**
- Semantic results first (higher quality)
- FTS results second (fill gaps)
- Remove duplicates by ID

### 3. MDX > Markdown

**Преимущества:**
- Interactive components (tabs, accordions, code playgrounds)
- Reusable components (callouts, cards, diagrams)
- Type-safe (TypeScript props)
- Better DX (JSX syntax)

**Trade-offs:**
- More complex build pipeline
- Requires React knowledge
- Slower compilation

**Recommendation:** Use MDX для knowledge base (интерактивность важна), plain Markdown для simple docs.

### 4. Documentation as Code

**Best practices:**
- Store docs in Git (version control)
- Docs in same repo as code (sync updates)
- PR workflow (review + approval)
- CI/CD (auto-deploy on merge)
- Linting (markdown-lint, link checker)

**Benefits:**
- Docs stay up-to-date
- Easy collaboration
- Audit trail
- Rollback capability

---

## Next Steps

### Immediate (This Sprint)

1. **Create basic knowledge base structure**
   - Setup Next.js app in `AIM/knowledge-base/`
   - Configure MDX processing pipeline
   - Create folder structure (`content/docs/`)

2. **Implement FlexSearch**
   - Build-time indexing script
   - Search API endpoint
   - Search dialog component

3. **Add first documentation**
   - Getting Started guide
   - API reference (basic)
   - Troubleshooting section

### Short-term (Next Sprint)

1. **Add versioning**
   - Version selector component
   - Version-specific content
   - Migration guides

2. **Implement analytics**
   - Page view tracking
   - Search query logging
   - Popular content dashboard

3. **Create contribution workflow**
   - GitHub PR template
   - Review guidelines
   - Auto-deploy on merge

### Long-term (Future Sprints)

1. **Migrate to MeiliSearch**
   - Setup MeiliSearch instance
   - Migrate indexing logic
   - Update search API

2. **Add semantic search**
   - Setup PostgreSQL + pgvector
   - Generate embeddings
   - Implement hybrid search

3. **Build AI assistant**
   - RAG pipeline
   - Chat interface
   - Context-aware responses

---

## Conclusion

Исследование показало, что современные knowledge base системы используют:

1. **MDX** для интерактивности и переиспользования компонентов
2. **Build-time indexing** для скорости и низкой стоимости
3. **Hybrid search** (semantic + FTS) для лучшей релевантности
4. **Three-layer navigation** (dimensions → views → content) для масштабируемости

**Рекомендация для AIM:**
- Start simple: FlexSearch + MDX + Next.js
- Scale smart: MeiliSearch при росте
- Future-proof: Hybrid search для AI assistant

**Estimated timeline:** 6 weeks (1 developer)  
**Estimated cost:** $0-50/month (depending on scale)

---

## Sources

### GitHub Repositories
1. docs-generator (rabinarayanpatra) - FlexSearch + MDX
2. docs.dblayer.dev (scorcism) - Build-time indexing
3. commonbase (your-commonbase) - Semantic search + pgvector

### Articles
1. "How to Build Documentation Aggregation" - OneUpTime (2026)
2. "Using Markdown for Technical Writing" - mdkit (2026)
3. "Documentation Strategy: A 2026 Playbook" - Docsio (2026)
4. "How to organize team documentation" - Plane Blog (2026)
5. "How to structure your knowledge base" - Plane Blog (2026)
6. "How to Structure Large Documentation Projects" - Toflio (2026)
7. "Building a Knowledge Base Information Architecture" - knowledge-base.software (2025)
8. "Documentation Structure" - chubes.net (2026)

### Tools
- FlexSearch: https://github.com/nextapps-de/flexsearch
- MeiliSearch: https://www.meilisearch.com/
- pgvector: https://github.com/pgvector/pgvector
- next-mdx-remote: https://github.com/hashicorp/next-mdx-remote
- Docusaurus: https://docusaurus.io/
- Nextra: https://nextra.site/

