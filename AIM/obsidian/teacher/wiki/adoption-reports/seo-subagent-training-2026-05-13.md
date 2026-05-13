# SEO Subagent Training Report

**Date:** 2026-05-13  
**Subagent:** SEO (Search Engine Optimization)  
**Training Method:** Domain-specific research with GitHub analysis

---

## Phase 1: Domain-Specific Research

### Queries Executed (4)
1. `seo analysis python`
2. `serp api python`
3. `keyword research python`
4. `backlink analysis python`

### Total Repos Found: 19

---

## Phase 2: Top Repos Analysis

### By Stars (Top 5)
1. **how-to-scrape-google-trends** (2525 stars)
   - Oxylabs tutorial for Google Trends scraping
   - Skills extracted: 0 (tutorial, not library)
   
2. **how-to-scrape-google-scholar** (1603 stars)
   - Oxylabs tutorial for Google Scholar scraping
   - Skills extracted: 0 (tutorial, not library)
   
3. **advertools** (1390 stars) ⭐
   - Online marketing productivity and analysis tools
   - Skills extracted: 6 (Caching: 4, Rate Limiting: 1, Retry: 1)
   - Average quality: 70.8/100
   
4. **seo-audits-toolkit** (792 stars)
   - SEO & Security Audit toolkit
   - Skills extracted: 0 (syntax errors)
   
5. **google-search-results-python** (737 stars)
   - SerpApi Python client
   - Skills extracted: 0 (simple wrapper)

---

## Phase 3: Key Findings from advertools

### What is advertools?

**Philosophy:** UNIX-style modular tools for digital marketing
- Do one thing and do it well
- Work together as pipeline
- Handle DataFrames (universal interface)

### Core Capabilities

**1. SEM Campaign Management**
- Keyword generation (not research)
- Ad creation and management
- Landing page mapping
- Campaign structure optimization

**2. SEO Analysis**
- Website crawling
- Sitemap parsing
- robots.txt testing
- URL structure analysis
- Meta tags extraction

**3. Text Analysis**
- Hashtag extraction
- Emoji analysis
- Word frequency
- Text cleaning

**4. SERP Analysis**
- Google Trends scraping
- Search results parsing
- Competitor analysis

### Architecture Patterns Found

1. **DataFrame-First Design**
   - All functions return pandas DataFrames
   - Universal interface for data manipulation
   - Easy integration with visualization tools

2. **Modular Functions**
   - Each function does one thing
   - Can be combined in pipelines
   - Independent execution

3. **Caching** (4 instances, quality: 70.8/100)
   - Used for API responses
   - Reduces redundant requests

4. **Rate Limiting** (1 instance)
   - Controls request rate to APIs

5. **Retry Logic** (1 instance)
   - Handles transient failures

---

## Phase 4: Other Notable Repos

### serpapi/google-search-results-python (737 stars)
- Official SerpApi Python client
- Google Search Results via SERP API
- Simple wrapper, no advanced patterns

### chukhraiartur/seo-keyword-research-tool (153 stars)
- Google Autocomplete scraping
- People Also Ask extraction
- Related Searches extraction

### ecoron/SerpScrap (271 stars)
- Multi-search-engine scraper
- Extract URLs, titles, snippets
- Rich snippet detection
- Automated screenshots

---

## Phase 5: What to Adopt for SEO Subagent

### 1. DataFrame-First Architecture ✅
- **Why:** Universal interface, easy integration
- **How:** All SEO functions return pandas DataFrames
- **Pattern:** advertools approach

### 2. Modular Function Design ✅
- **Why:** Flexibility, reusability
- **How:** Each SEO task = separate function
- **Functions:**
  - `crawl_website()` - Spider websites
  - `parse_sitemap()` - Extract URLs from sitemaps
  - `test_robots()` - Check robots.txt rules
  - `extract_meta()` - Get meta tags
  - `analyze_serp()` - Parse search results
  - `generate_keywords()` - Keyword expansion
  - `check_backlinks()` - Backlink analysis

### 3. SERP API Integration ✅
- **Why:** Real-time search data
- **How:** Integrate SerpApi client
- **Pattern:** google-search-results-python

### 4. Caching & Rate Limiting ✅
- **Why:** API cost control, avoid bans
- **How:** Cache SERP results, limit requests
- **Pattern:** advertools caching

---

## Phase 6: Implementation Plan

### Step 1: Create SEO Module Structure
```
AIM/src/aim/subagents/seo/
├── analyzer.py           # Main SEO analyzer
├── crawlers/
│   ├── website.py        # Website crawler
│   ├── sitemap.py        # Sitemap parser
│   └── robots.py         # robots.txt checker
├── serp/
│   ├── client.py         # SerpApi client
│   ├── parser.py         # SERP parser
│   └── trends.py         # Google Trends
├── keywords/
│   ├── generator.py      # Keyword generation
│   ├── research.py       # Keyword research
│   └── clustering.py     # Keyword clustering
├── backlinks/
│   ├── analyzer.py       # Backlink analysis
│   └── checker.py        # Link quality check
└── utils/
    ├── cache.py          # Caching layer
    └── rate_limiter.py   # Rate limiting
```

### Step 2: Adopt Patterns from advertools
- [x] DataFrame-first design
- [x] Modular functions
- [x] Caching (4 instances, 70.8/100 quality)
- [x] Rate limiting (1 instance)
- [x] Retry logic (1 instance)
- [ ] Website crawling
- [ ] Sitemap parsing
- [ ] SERP analysis

### Step 3: Integrate SerpApi
- Use google-search-results-python (737 stars)
- Real-time SERP data
- Google, Bing, Yahoo support

---

## Comparison: Generic Patterns vs Domain-Specific

### Generic Patterns Found
- ✅ Caching (4 instances) - useful for API responses
- ✅ Rate Limiting (1 instance) - useful for API control
- ✅ Retry (1 instance) - useful for transient failures

### Domain-Specific Patterns Found
- ✅ DataFrame-first architecture (advertools)
- ✅ Modular function design (UNIX philosophy)
- ✅ Website crawling patterns
- ✅ Sitemap parsing
- ✅ robots.txt testing
- ✅ SERP analysis
- ✅ Keyword generation

---

## Next Steps

1. **Install advertools** - `pip install advertools`
2. **Study Core Functions** - crawl, sitemap, robots, keywords
3. **Integrate SerpApi** - Real-time SERP data
4. **Create SEO Analyzer** - Combine all functions
5. **Test on Real Sites** - Validate functionality

---

## Metrics

- **Repos analyzed:** 5
- **Skills extracted:** 6
- **Average quality:** 70.8/100
- **Key library:** advertools (1390 stars)
- **Time spent:** ~30 seconds
- **Cost:** GitHub API (free)

---

## Conclusion

✅ **Found production-ready SEO library!**

- advertools (1390 stars) - comprehensive SEO toolkit
- DataFrame-first design (universal interface)
- Modular functions (UNIX philosophy)
- Real patterns: crawling, sitemap, robots, SERP

⚠️ **Lower skill count than Ads**

- Only 6 skills extracted (vs 1,154 for Ads)
- Reason: advertools is more about domain functions than resilience patterns
- Focus: SEO-specific capabilities, not generic patterns

**Conclusion:** SEO subagent needs advertools + SerpApi integration.
