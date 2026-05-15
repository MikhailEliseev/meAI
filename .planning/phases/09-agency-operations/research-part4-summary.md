# Research Part 4: Knowledge Base - Quick Summary

**Date:** 2026-05-15  
**Status:** ✅ COMPLETED  
**Full Report:** `research-part4-knowledge.md` (739 lines)

---

## TL;DR

Нашёл 3 production-ready решения для knowledge base:

1. **docs-generator** - FlexSearch (client-side, $0/month)
2. **docs.dblayer.dev** - Build-time indexing (advanced cleaning)
3. **commonbase** - Semantic search (pgvector + OpenAI, $25-50/month)

**Recommendation:** Start с FlexSearch → Scale к MeiliSearch → Add semantic search для AI.

---

## Top 3 Repos (Cloned & Analyzed)

### 1. docs-generator ⭐ Best Overall
- **Path:** `~/temp/research-repos/knowledge-base/docs-generator`
- **Stack:** Next.js 16, FlexSearch, MDX
- **Key Files:**
  - `src/lib/search.ts` - FlexSearch setup
  - `src/lib/mdx.ts` - MDX processing pipeline
  - `src/components/search/search-dialog.tsx` - Search UI
- **What to copy:**
  - FlexSearch multi-field indexing
  - Markdown stripping function
  - Search dialog с keyboard shortcuts
  - MDX rehype/remark plugins

### 2. docs.dblayer.dev ⭐ Best Indexing
- **Path:** `~/temp/research-repos/knowledge-base/docs.dblayer.dev`
- **Stack:** Next.js 15, Custom indexing
- **Key Files:**
  - `scripts/content.ts` - Build-time index generation
  - `lib/markdown.ts` - MDX compilation
  - `components/navigation/search.tsx` - Search component
- **What to copy:**
  - Build-time indexing script
  - Advanced content cleaning
  - Custom MDX components removal
  - Keyword extraction strategy

### 3. commonbase ⭐ Best Semantic Search
- **Path:** `~/temp/research-repos/knowledge-base/commonbase`
- **Stack:** Next.js 15, PostgreSQL + pgvector, OpenAI
- **Key Files:**
  - `commonbase-next/src/app/api/search/route.ts` - Hybrid search
  - `commonbase-next/src/lib/embeddings.ts` - OpenAI embeddings
  - `commonbase-next/src/lib/db/schema.ts` - pgvector schema
- **What to copy:**
  - Hybrid search pattern (semantic + FTS)
  - OpenAI embeddings integration
  - pgvector setup
  - Deduplication strategy

---

## Architecture Patterns

### Search Strategies

| Strategy | Cost | Speed | Quality | Use Case |
|----------|------|-------|---------|----------|
| FlexSearch (client) | $0 | Instant | Good | <1000 pages |
| MeiliSearch (server) | $25-50 | <50ms | Great | >1000 pages |
| Hybrid (semantic+FTS) | $25-50 | ~200ms | Best | AI assistant |

### Navigation Patterns

1. **Hierarchical** - Categories → Subcategories → Pages (API docs)
2. **Hub-and-Spoke** - Landing page → Related pages (Guides)
3. **Topic Clusters** - Pillar page → Cluster pages (Tutorials)

### Folder Structure

```
docs/
├── index.md                    # Landing
├── getting-started/            # Onboarding
├── guides/                     # How-to
├── reference/                  # API docs
├── concepts/                   # Explanation
└── assets/                     # Images
```

---

## Implementation Plan

### Phase 1: Basic KB (Week 1-2)
- Next.js 15 + MDX
- FlexSearch (client-side)
- Search dialog (Cmd+K)
- Syntax highlighting
- **Cost:** $0/month

### Phase 2: Advanced (Week 3-4)
- Versioning
- Analytics
- AI assistant (basic)
- Contribution workflow
- **Cost:** $0/month

### Phase 3: Semantic (Week 5-6)
- PostgreSQL + pgvector
- OpenAI embeddings
- Hybrid search
- **Cost:** $25-50/month

---

## Key Code Snippets

### FlexSearch Setup
```typescript
// Multi-field indexing с приоритетами
const searchIndex = new Index({
  preset: 'match',
  tokenize: 'forward',
  cache: true,
})

searchIndex.add(id, title)        // Highest
searchIndex.add(id, description)
searchIndex.add(id, headings)
searchIndex.add(id, content)      // Lowest
```

### Markdown Stripping
```typescript
function stripMarkdown(md: string): string {
  return md
    .replace(/^---[\s\S]*?---/, '')     // Frontmatter
    .replace(/```[\s\S]*?```/g, '')     // Code blocks
    .replace(/`[^`]+`/g, '')            // Inline code
    .replace(/!\[.*?\]\(.*?\)/g, '')    // Images
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Links
    .replace(/\s+/g, ' ')
    .trim()
}
```

### Hybrid Search
```typescript
// 1. Semantic search
const embedding = await generateEmbedding(query)
const semantic = await db
  .where(sql`1 - (embedding <=> ${embedding}::vector) > 0.7`)
  .orderBy(sql`embedding <=> ${embedding}::vector`)

// 2. Full-text search
const fts = await db
  .where(sql`to_tsvector('english', data) @@ plainto_tsquery('english', ${query})`)
  .orderBy(sql`ts_rank(...)`)

// 3. Deduplicate (semantic first)
return deduplicate([...semantic, ...fts])
```

---

## Dependencies

### Core
```json
{
  "next": "^15.0.0",
  "next-mdx-remote": "^5.0.0",
  "gray-matter": "^4.0.3",
  "flexsearch": "^0.8.212"
}
```

### MDX Processing
```json
{
  "remark-gfm": "^4.0.0",
  "rehype-slug": "^6.0.0",
  "rehype-autolink-headings": "^7.0.0",
  "rehype-pretty-code": "^0.13.0",
  "rehype-katex": "^7.0.0"
}
```

### Semantic Search (Optional)
```json
{
  "openai": "^5.20.1",
  "drizzle-orm": "^0.44.5",
  "pg": "^8.11.0"
}
```

---

## Next Actions

1. ✅ Research completed (3 repos cloned, 10+ articles analyzed)
2. ⏳ Create basic KB structure in `AIM/knowledge-base/`
3. ⏳ Copy FlexSearch setup from docs-generator
4. ⏳ Copy MDX pipeline from docs-generator
5. ⏳ Copy build-time indexing from docs.dblayer.dev
6. ⏳ Test with sample documentation

---

## Files to Reference

**Full report:** `.planning/phases/09-agency-operations/research-part4-knowledge.md`  
**Cloned repos:** `~/temp/research-repos/knowledge-base/`
- `docs-generator/` - FlexSearch + MDX
- `docs.dblayer.dev/` - Build-time indexing
- `commonbase/` - Semantic search

**Key files to copy:**
1. `docs-generator/src/lib/search.ts` → FlexSearch setup
2. `docs-generator/src/lib/mdx.ts` → MDX pipeline
3. `docs-generator/src/components/search/search-dialog.tsx` → Search UI
4. `docs.dblayer.dev/scripts/content.ts` → Indexing script
5. `commonbase/commonbase-next/src/app/api/search/route.ts` → Hybrid search

---

**Total time:** ~2 hours  
**Quality:** High (production-ready code analyzed)  
**Ready for:** Implementation (Phase 1)
