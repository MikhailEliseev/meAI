"""
SkillSelector - Extract skills from GitHub repositories.

Identifies:
- Resilience patterns (circuit breaker, retry, rate limiting, caching)
- Best practices (error handling, async patterns)
- Code quality metrics
- Reusable implementations
"""

import ast
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class Skill:
    """Extracted skill from repository."""

    name: str
    description: str
    code_example: str
    quality_score: float  # 0-100
    source_repo: str
    file_path: str


@dataclass
class GitHubRepo:
    """GitHub repository metadata."""

    url: str
    stars: int
    description: str
    language: str = "Python"


class SkillSelector:
    """
    Extract skills from GitHub repositories.

    Responsibilities:
    - Search GitHub for relevant repositories
    - Clone repositories locally
    - Extract patterns and best practices
    - Score code quality
    - Identify reusable implementations
    """

    def __init__(self):
        self.logger = logger.bind(component="skill_selector")

        # Pattern signatures for detection (generic patterns)
        self.pattern_signatures = {
            "circuit_breaker": ["CircuitBreaker", "pybreaker", "fail_max", "reset_timeout"],
            "retry": ["retry", "tenacity", "stop_after_attempt", "wait_exponential"],
            "rate_limiting": ["AsyncLimiter", "aiolimiter", "RateLimiter", "rate_limit"],
            "caching": ["cached", "aiocache", "@cache", "ttl"],
        }

        # Domain-specific import signatures per subagent type
        self.domain_import_signatures = {
            "ci-content": [
                "trafilatura",
                "BeautifulSoup",
                "lxml",
                "scrapy",
                "crawlee",
            ],
            "ci-tech": [
                "lighthouse",
                "playwright",
                "selenium",
            ],
            "keyword-research": [
                "semrush",
                "ahrefs",
                "serpapi",
            ],
            "seo": [
                "pandas",
                "requests",
                "httpx",
            ],
            "content": [
                "openai",
                "anthropic",
                "langchain",
            ],
            "ads": [
                "yandex",
                "google",
                "facebook",
            ],
        }

        # Domain-specific pattern signatures per subagent type
        self.domain_pattern_signatures = {
            "ci-content": {
                "content_extraction": [
                    "extract", "parse", "scrape", "trafilatura",
                    "beautifulsoup", "html", "text", "article"
                ],
                "seo_analysis": [
                    "meta", "title", "description", "keywords",
                    "heading", "h1", "h2", "seo", "optimize"
                ],
                "keyword_density": [
                    "density", "frequency", "keyword", "count",
                    "occurrence", "distribution"
                ],
                "competitor_comparison": [
                    "compare", "competitor", "gap", "difference",
                    "similarity", "overlap"
                ],
            },
            "ci-tech": {
                "lighthouse_audit": [
                    "lighthouse", "performance", "vitals", "audit",
                    "lcp", "fid", "cls", "speed"
                ],
                "crawl_analysis": [
                    "crawl", "sitemap", "robots", "indexing",
                    "spider", "discover"
                ],
            },
            "ads": {
                "mcp_server": ["mcp.server.Server", "stdio", "@server.tool", "server.list_tools"],
                "api_client": ["httpx.AsyncClient", "timeout=", "headers=", "async with"],
                "oauth": ["OAuth", "token", "refresh_token", "access_token"],
                "tool_registration": ["@server.tool", "tool_name", "tool_description"],
            },
            "seo": {
                "dataframe_first": ["pd.DataFrame", "return df", "to_frame()", "DataFrame("],
                "modular_functions": ["def crawl_", "def parse_", "def extract_", "def analyze_"],
                "sitemap": ["sitemap.xml", "urlset", "loc", "lastmod"],
                "robots_txt": ["robots.txt", "User-agent", "Disallow", "Allow"],
            },
            "analytics": {
                "event_driven": ["event_bus", "emit", "on(", "EventEmitter", "publish"],
                "real_time": ["stream", "aggregate", "window", "real_time"],
                "metrics": ["metric", "gauge", "counter", "histogram", "prometheus"],
                "multi_layer_cache": ["redis", "in_memory", "cache_layer", "cache_strategy"],
            },
            "content": {
                "llm_api": ["openai", "anthropic", "gemini", "ChatCompletion", "messages"],
                "content_generation": ["generate", "prompt", "template", "content_type"],
                "content_optimization": ["seo_score", "readability", "keyword_density"],
            },
            "gap_detection": {
                "serp_overlap": ["serp", "overlap", "intersection", "keyword_match"],
                "keyword_gap": ["keyword_gap", "missing_keywords", "competitor_keywords"],
                "content_gap": ["content_gap", "missing_topics", "topic_coverage"],
            },
            "prioritization": {
                "mcda": ["mcda", "multi_criteria", "ahp", "topsis", "weighted_sum"],
                "priority_queue": ["priority_queue", "heapq", "PriorityQueue", "redis_queue"],
                "scoring": ["score", "weight", "rank", "priority_score"],
            },
            "social": {
                "telegram_bot": ["telegram", "Bot", "Updater", "CommandHandler", "MessageHandler"],
                "rate_limiting_api": ["rate_limit", "30", "per_second", "api_limit"],
                "multi_platform": ["telegram", "vk", "platform", "adapter"],
            },
        }

        # Domain-specific queries per subagent type
        self.domain_queries = {
            "ads": [
                "yandex direct api python",
                "google ads api python",
                "facebook ads api python",
                "advertising campaign automation",
            ],
            "seo": [
                "seo analysis python",
                "serp api python",
                "keyword research python",
                "backlink analysis python",
            ],
            "content": [
                "content generation python",
                "ai content writer python",
                "blog automation python",
                "content optimization python",
            ],
            "analytics": [
                "web analytics python",
                "google analytics api python",
                "yandex metrika api python",
                "data visualization python",
            ],
            "gap_detection": [
                "content gap analysis python",
                "competitor analysis python",
                "serp overlap python",
                "keyword gap python",
            ],
            "prioritization": [
                "task prioritization python",
                "scoring algorithm python",
                "multi-criteria decision python",
                "priority queue python",
            ],
            "social": [
                "social media api python",
                "telegram bot python",
                "vk api python",
                "social media automation python",
            ],
            "keyword-research": [
                "semrush api python",
                "ahrefs api python",
                "keyword research tool python",
                "serp api keyword data python",
            ],
            "ci-content": [
                "python seo analyzer",
                "content scraper python",
                "competitor analysis tool python",
                "web scraping beautifulsoup python",
                "trafilatura content extraction python",
            ],
            "ci-tech": [
                "lighthouse python",
                "playwright python seo",
                "technical seo audit python",
                "core web vitals python",
                "page speed analysis python",
            ],
            "content-gap": [
                "content gap analysis python",
                "serp overlap python",
                "keyword gap analysis python",
                "competitor content analysis python",
                "topic clustering python",
            ],
            "backlink": [
                "backlink analysis python",
                "link building python",
                "domain authority python",
                "ahrefs api python",
                "moz api python",
            ],
            "content-brief": [
                "content brief generator python",
                "seo content brief python",
                "content outline generator python",
                "serp analysis content brief python",
                "competitor content analysis python",
            ],
            "ad-copy": [
                "ad copy generator python",
                "advertising copywriting python",
                "ppc ad generator python",
                "yandex direct ad copy python",
                "google ads copy generator python",
            ],
            "traffic-analyzer": [
                "google analytics api python",
                "yandex metrika api python",
                "web analytics python",
                "traffic analysis python",
                "user behavior analytics python",
            ],
            "conversion-tracker": [
                "conversion tracking python",
                "goal tracking analytics python",
                "funnel analysis python",
                "attribution modeling python",
                "revenue tracking python",
            ],
            "schema-generator": [
                "schema.org generator python",
                "structured data python",
                "json-ld generator python",
                "rich snippets python",
                "seo schema markup python",
            ],
            "quality-checker": [
                "content quality checker python",
                "seo content analyzer python",
                "readability checker python",
                "grammar checker python",
                "plagiarism checker python",
            ],
            "landing-page": [
                "landing page analyzer python",
                "conversion optimization python",
                "page speed analysis python",
                "lighthouse python",
                "ux analysis python",
            ],
            "bid-optimizer": [
                "bid optimization python",
                "ppc bid management python",
                "google ads bidding python",
                "yandex direct bidding python",
                "automated bidding python",
            ],
            "report-generator": [
                "marketing report generator python",
                "analytics dashboard python",
                "data visualization python",
                "pdf report generator python",
                "automated reporting python",
            ],
            "calendar-manager": [
                "content calendar python",
                "social media scheduler python",
                "editorial calendar python",
                "publishing schedule python",
                "content planning python",
            ],
        }

    async def research_domain_specific(
        self, subagent_name: str, domain: str
    ) -> dict[str, list[GitHubRepo]]:
        """
        Deep research for domain-specific solutions.

        Uses Exa MCP tools for comprehensive research and GitHub search
        for specialized repositories.

        Args:
            subagent_name: Name of subagent (e.g., "ads", "seo")
            domain: Domain description (e.g., "advertising automation")

        Returns:
            Dict mapping query to list of repos found
        """
        self.logger.info(
            "domain_research_start",
            subagent=subagent_name,
            domain=domain,
        )

        results = {}

        # Get domain-specific queries for this subagent
        queries = self.domain_queries.get(subagent_name, [])

        if not queries:
            self.logger.warning(
                "no_domain_queries",
                subagent=subagent_name,
                fallback="generic search",
            )
            queries = [domain]

        # Search GitHub for each domain-specific query
        for query in queries:
            repos = await self.search_github_repos(query, max_results=5)
            if repos:
                results[query] = repos
                self.logger.info(
                    "domain_query_complete",
                    query=query,
                    repos_found=len(repos),
                )

        total_repos = sum(len(repos) for repos in results.values())
        self.logger.info(
            "domain_research_complete",
            subagent=subagent_name,
            queries_executed=len(queries),
            total_repos=total_repos,
        )

        return results

    async def research_and_clone(
        self, subagent_name: str, domain: str
    ) -> dict[str, Path]:
        """
        Research domain-specific solutions AND clone ALL repos.

        This is the CORRECT workflow:
        1. Search GitHub for repos
        2. Clone ALL found repos to ~/temp/research-repos/
        3. Return mapping of URL -> local path

        Args:
            subagent_name: Name of subagent (e.g., "ads", "seo")
            domain: Domain description (e.g., "advertising automation")

        Returns:
            Dict mapping repo URL to local clone path
        """
        self.logger.info(
            "research_and_clone_start",
            subagent=subagent_name,
            domain=domain,
        )

        # Step 1: Research (search GitHub)
        results = await self.research_domain_specific(subagent_name, domain)

        # Step 2: Clone ALL repos
        cloned_repos = {}
        base_path = Path.home() / "temp" / "research-repos"
        base_path.mkdir(parents=True, exist_ok=True)

        for query, repos in results.items():
            for repo in repos:
                # Extract repo name from URL
                repo_name = repo.url.rstrip("/").split("/")[-1]
                clone_path = base_path / repo_name

                # Skip if already cloned
                if clone_path.exists():
                    self.logger.info(
                        "repo_already_cloned",
                        url=repo.url,
                        path=str(clone_path),
                    )
                    cloned_repos[repo.url] = clone_path
                    continue

                # Clone repo
                try:
                    await self.clone_repo(repo.url, clone_path)
                    cloned_repos[repo.url] = clone_path
                    self.logger.info(
                        "repo_cloned_success",
                        url=repo.url,
                        path=str(clone_path),
                    )
                except Exception as e:
                    self.logger.error(
                        "repo_clone_failed",
                        url=repo.url,
                        error=str(e),
                    )
                    # Continue with other repos even if one fails

        self.logger.info(
            "research_and_clone_complete",
            subagent=subagent_name,
            total_repos_found=sum(len(repos) for repos in results.values()),
            repos_cloned=len(cloned_repos),
        )

        return cloned_repos

    async def search_github_repos(
        self, query: str, max_results: int = 10
    ) -> list[GitHubRepo]:
        """
        Search GitHub repositories.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of GitHub repositories
        """
        self.logger.info("searching_github", query=query, max_results=max_results)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": f"{query} language:python",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": max_results,
                    },
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    self.logger.warning(
                        "github_search_failed",
                        status_code=response.status_code,
                        query=query,
                    )
                    return []

                data = response.json()
                repos = []

                for item in data.get("items", []):
                    repos.append(
                        GitHubRepo(
                            url=item["html_url"],
                            stars=item["stargazers_count"],
                            description=item.get("description", ""),
                            language=item.get("language", "Python"),
                        )
                    )

                self.logger.info("github_search_complete", repos_found=len(repos))
                return repos

        except Exception as e:
            self.logger.error("github_search_error", error=str(e), query=query)
            return []

    async def clone_repo(self, repo_url: str, clone_path: Path) -> None:
        """
        Clone GitHub repository.

        Args:
            repo_url: Repository URL
            clone_path: Local path to clone to
        """
        self.logger.info("cloning_repo", url=repo_url, path=str(clone_path))

        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(clone_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.logger.info("repo_cloned", path=str(clone_path))

        except subprocess.CalledProcessError as e:
            self.logger.error(
                "clone_failed",
                url=repo_url,
                error=e.stderr,
            )
            raise

    async def extract_skills(self, repo_path: Path, subagent_type: str = None) -> list[Skill]:
        """
        Extract skills from repository.

        Args:
            repo_path: Path to repository
            subagent_type: Type of subagent (e.g., "ads", "seo") for domain-specific extraction

        Returns:
            List of extracted skills
        """
        self.logger.info("extracting_skills", repo_path=str(repo_path), subagent_type=subagent_type)

        skills = []

        # Scan all Python files
        for file_path in repo_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                # Detect patterns in file (with subagent_type for domain-specific patterns)
                detected_patterns = self._detect_patterns(content, tree, subagent_type)

                for pattern_name, pattern_info in detected_patterns.items():
                    skill = Skill(
                        name=pattern_info["name"],
                        description=pattern_info["description"],
                        code_example=pattern_info["code"],
                        quality_score=pattern_info["quality_score"],
                        source_repo=str(repo_path),
                        file_path=str(file_path.relative_to(repo_path)),
                    )
                    skills.append(skill)

            except (SyntaxError, UnicodeDecodeError) as e:
                self.logger.warning(
                    "file_parse_error",
                    file_path=str(file_path),
                    error=str(e),
                )
                continue

        self.logger.info("skills_extracted", count=len(skills))
        return skills

    def _detect_patterns(self, content: str, tree: ast.AST, subagent_type: str = None) -> dict:
        """
        Detect patterns in code.

        Args:
            content: File content
            tree: AST tree
            subagent_type: Type of subagent for domain-specific pattern detection

        Returns:
            Dict of detected patterns
        """
        patterns = {}

        # SKIP generic patterns (circuit breaker, retry, rate limiting, caching)
        # These are already in base.py and should NOT be extracted again
        # We only want domain-specific patterns for each subagent

        # Extract domain-specific functions by imports (NEW APPROACH)
        if subagent_type and subagent_type in self.domain_import_signatures:
            target_imports = self.domain_import_signatures[subagent_type]
            functions = self._extract_functions_using_imports(content, target_imports)

            for func in functions:
                pattern_key = f"{subagent_type}_{func['name']}"
                patterns[pattern_key] = {
                    "name": f"{subagent_type.title()} - {func['name'].replace('_', ' ').title()}",
                    "description": func['docstring'] or f"Function using {', '.join(func['imports_used'])}",
                    "code": func['code'],
                    "quality_score": self._score_pattern(func['code'], func['name']),
                }

        return patterns

    def _has_pattern(self, content: str, pattern_name: str) -> bool:
        """Check if content contains pattern."""
        signatures = self.pattern_signatures.get(pattern_name, [])
        return any(sig in content for sig in signatures)

    def _extract_pattern_code(self, content: str, pattern_name: str) -> str:
        """Extract code example for pattern."""
        signatures = self.pattern_signatures.get(pattern_name, [])

        # Try to extract full function/class containing the pattern
        for sig in signatures:
            if sig in content:
                # Find the signature position
                sig_pos = content.find(sig)

                # Search backwards for function/class definition
                lines = content[:sig_pos].split('\n')
                start_line_idx = None

                for i in range(len(lines) - 1, -1, -1):
                    line = lines[i]
                    # Look for function or class definition
                    if line.strip().startswith('def ') or line.strip().startswith('async def ') or line.strip().startswith('class '):
                        start_line_idx = i
                        break

                if start_line_idx is not None:
                    # Found function/class start, now find the end
                    start_pos = len('\n'.join(lines[:start_line_idx])) + (1 if start_line_idx > 0 else 0)

                    # Find end of function/class (next def/class at same or lower indentation)
                    remaining = content[start_pos:]
                    remaining_lines = remaining.split('\n')

                    if not remaining_lines:
                        return content[start_pos:]

                    # Get indentation of the definition
                    first_line = remaining_lines[0]
                    def_indent = len(first_line) - len(first_line.lstrip())

                    end_line_idx = len(remaining_lines)
                    for i in range(1, len(remaining_lines)):
                        line = remaining_lines[i]
                        if line.strip():  # Non-empty line
                            line_indent = len(line) - len(line.lstrip())
                            # If we find a line at same or lower indentation that starts a new def/class
                            if line_indent <= def_indent and (line.strip().startswith('def ') or
                                                              line.strip().startswith('async def ') or
                                                              line.strip().startswith('class ')):
                                end_line_idx = i
                                break

                    # Extract the full function/class
                    extracted = '\n'.join(remaining_lines[:end_line_idx])
                    return extracted.strip()
                else:
                    # Fallback: return context around signature (larger window)
                    start = max(0, sig_pos - 200)
                    end = min(len(content), sig_pos + 1000)
                    return content[start:end].strip()

        return ""

    def _score_pattern(self, content: str, pattern_name: str) -> float:
        """
        Score pattern implementation quality.

        Factors:
        - Completeness (has error handling, configuration)
        - Best practices (async, type hints)
        - Documentation (docstrings, comments)

        Returns:
            Quality score (0-100)
        """
        score = 50.0  # Base score

        # Check for error handling
        if "try:" in content and "except" in content:
            score += 15.0

        # Check for async
        if "async def" in content or "await" in content:
            score += 10.0

        # Check for type hints
        if "->" in content and ":" in content:
            score += 10.0

        # Check for docstrings
        if '"""' in content or "'''" in content:
            score += 10.0

        # Check for configuration
        if "config" in content.lower() or "settings" in content.lower():
            score += 5.0

        return min(score, 100.0)

    def _has_pattern_from_signatures(self, content: str, signatures: list[str]) -> bool:
        """Check if content contains any of the given signatures."""
        return any(sig in content for sig in signatures)

    def _extract_functions_using_imports(
        self,
        content: str,
        target_imports: list[str]
    ) -> list[dict]:
        """
        Extract functions that use specific imports.

        Args:
            content: File content
            target_imports: List of import names to look for
                           (e.g., ["trafilatura", "BeautifulSoup"])

        Returns:
            List of functions using these imports
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        # Step 1: Find all imports in file
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                for alias in node.names:
                    imports.add(alias.name)

        # Step 2: Check if any target imports present
        matching_imports = [imp for imp in target_imports if any(imp in file_imp for file_imp in imports)]
        if not matching_imports:
            return []

        # Step 3: Find functions using these imports
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                try:
                    func_code = ast.get_source_segment(content, node)
                    if not func_code:
                        continue

                    # Check if function uses target imports
                    uses_import = any(imp in func_code for imp in matching_imports)

                    if uses_import:
                        functions.append({
                            "name": node.name,
                            "code": func_code,
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                            "docstring": ast.get_docstring(node) or "",
                            "imports_used": matching_imports,
                        })
                except (ValueError, AttributeError):
                    continue

        return functions

    def _extract_pattern_code_from_signatures(self, content: str, signatures: list[str]) -> str:
        """Extract code example for pattern from signatures."""
        # Find ALL signature matches and extract functions
        all_matches = []

        for sig in signatures:
            pos = 0
            while True:
                sig_pos = content.find(sig, pos)
                if sig_pos == -1:
                    break

                # Check if signature is in docstring/comment
                lines_before = content[:sig_pos].split('\n')
                if lines_before:
                    last_line = lines_before[-1]
                    # Skip if inside docstring or comment
                    if '"""' in last_line or "'''" in last_line or last_line.strip().startswith('#'):
                        pos = sig_pos + 1
                        continue

                # Search backwards for function/class definition
                start_line_idx = None
                for i in range(len(lines_before) - 1, -1, -1):
                    line = lines_before[i]
                    # Look for function or class definition
                    if line.strip().startswith('def ') or line.strip().startswith('async def ') or line.strip().startswith('class '):
                        start_line_idx = i
                        break

                if start_line_idx is not None:
                    # Found function/class start, now find the end
                    start_pos = len('\n'.join(lines_before[:start_line_idx])) + (1 if start_line_idx > 0 else 0)

                    # Find end of function/class (next def/class at same or lower indentation)
                    remaining = content[start_pos:]
                    remaining_lines = remaining.split('\n')

                    if not remaining_lines:
                        pos = sig_pos + 1
                        continue

                    # Get indentation of the definition
                    first_line = remaining_lines[0]
                    def_indent = len(first_line) - len(first_line.lstrip())

                    end_line_idx = len(remaining_lines)
                    for i in range(1, len(remaining_lines)):
                        line = remaining_lines[i]
                        if line.strip():  # Non-empty line
                            line_indent = len(line) - len(line.lstrip())
                            # If we find a line at same or lower indentation that starts a new def/class
                            if line_indent <= def_indent and (line.strip().startswith('def ') or
                                                              line.strip().startswith('async def ') or
                                                              line.strip().startswith('class ')):
                                end_line_idx = i
                                break

                    # Extract the full function/class
                    extracted = '\n'.join(remaining_lines[:end_line_idx])
                    all_matches.append(extracted.strip())

                pos = sig_pos + 1

        # Return longest match (most complete implementation)
        if all_matches:
            return max(all_matches, key=len)

        return ""

    def _get_domain_pattern_description(self, subagent_type: str, pattern_name: str) -> str:
        """Get description for domain-specific pattern."""
        descriptions = {
            "ci-content": {
                "content_extraction": "Content extraction from web pages using trafilatura or BeautifulSoup",
                "seo_analysis": "SEO meta analysis (title, description, keywords, headings)",
                "keyword_density": "Keyword density calculation and frequency analysis",
                "competitor_comparison": "Competitor content comparison and gap detection",
            },
            "ci-tech": {
                "lighthouse_audit": "Lighthouse performance audit and Core Web Vitals analysis",
                "crawl_analysis": "Website crawl analysis (sitemap, robots.txt, indexing)",
            },
            "ads": {
                "mcp_server": "MCP server architecture for tool registration and communication",
                "api_client": "Async HTTP client pattern with timeout and header management",
                "oauth": "OAuth authentication flow with token refresh",
                "tool_registration": "Tool registration pattern for MCP server",
            },
            "seo": {
                "dataframe_first": "DataFrame-first design pattern for universal data interface",
                "modular_functions": "Modular function design following UNIX philosophy",
                "sitemap": "Sitemap parsing and URL extraction",
                "robots_txt": "Robots.txt parsing and rule checking",
            },
            "analytics": {
                "event_driven": "Event-driven architecture with event bus",
                "real_time": "Real-time data processing and streaming",
                "metrics": "Metrics collection and monitoring (Prometheus-style)",
                "multi_layer_cache": "Multi-layer caching strategy (Redis, in-memory, database)",
            },
            "content": {
                "llm_api": "LLM API integration (OpenAI, Anthropic, Gemini)",
                "content_generation": "Content generation workflow with prompts and templates",
                "content_optimization": "Content optimization for SEO and readability",
            },
            "gap_detection": {
                "serp_overlap": "SERP overlap analysis for keyword intersection",
                "keyword_gap": "Keyword gap detection between competitors",
                "content_gap": "Content gap analysis for missing topics",
            },
            "prioritization": {
                "mcda": "Multi-Criteria Decision Analysis methods (AHP, TOPSIS)",
                "priority_queue": "Priority queue implementation (heap-based or Redis)",
                "scoring": "Scoring algorithms with weights and ranking",
            },
            "social": {
                "telegram_bot": "Telegram Bot API integration with handlers",
                "rate_limiting_api": "Rate limiting for API compliance (30 msg/sec for Telegram)",
                "multi_platform": "Multi-platform support (Telegram, VK, etc.)",
            },
        }

        return descriptions.get(subagent_type, {}).get(
            pattern_name,
            f"Domain-specific pattern: {pattern_name}"
        )

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        if any(part.startswith(".") for part in file_path.parts):
            return True
        if "__pycache__" in file_path.parts:
            return True
        if "test" in file_path.name:
            return True
        return False
