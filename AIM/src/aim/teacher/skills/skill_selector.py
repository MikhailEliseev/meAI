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

        # Domain-specific pattern signatures per subagent type
        self.domain_pattern_signatures = {
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

        # Check for generic patterns (circuit breaker, retry, rate limiting, caching)
        if self._has_pattern(content, "circuit_breaker"):
            patterns["circuit_breaker"] = {
                "name": "Circuit Breaker",
                "description": "Prevents cascading failures by stopping requests to failing services",
                "code": self._extract_pattern_code(content, "circuit_breaker"),
                "quality_score": self._score_pattern(content, "circuit_breaker"),
            }

        if self._has_pattern(content, "retry"):
            patterns["retry"] = {
                "name": "Retry with Exponential Backoff",
                "description": "Automatically retries failed operations with increasing delays",
                "code": self._extract_pattern_code(content, "retry"),
                "quality_score": self._score_pattern(content, "retry"),
            }

        if self._has_pattern(content, "rate_limiting"):
            patterns["rate_limiting"] = {
                "name": "Rate Limiting",
                "description": "Controls request rate to prevent overwhelming services",
                "code": self._extract_pattern_code(content, "rate_limiting"),
                "quality_score": self._score_pattern(content, "rate_limiting"),
            }

        if self._has_pattern(content, "caching"):
            patterns["caching"] = {
                "name": "Caching",
                "description": "Stores responses to reduce redundant requests",
                "code": self._extract_pattern_code(content, "caching"),
                "quality_score": self._score_pattern(content, "caching"),
            }

        # Check for domain-specific patterns if subagent_type provided
        if subagent_type and subagent_type in self.domain_pattern_signatures:
            domain_patterns = self.domain_pattern_signatures[subagent_type]
            for pattern_name, signatures in domain_patterns.items():
                if self._has_pattern_from_signatures(content, signatures):
                    patterns[f"{subagent_type}_{pattern_name}"] = {
                        "name": f"{subagent_type.title()} - {pattern_name.replace('_', ' ').title()}",
                        "description": self._get_domain_pattern_description(subagent_type, pattern_name),
                        "code": self._extract_pattern_code_from_signatures(content, signatures),
                        "quality_score": self._score_pattern(content, pattern_name),
                    }

        return patterns

    def _has_pattern(self, content: str, pattern_name: str) -> bool:
        """Check if content contains pattern."""
        signatures = self.pattern_signatures.get(pattern_name, [])
        return any(sig in content for sig in signatures)

    def _extract_pattern_code(self, content: str, pattern_name: str) -> str:
        """Extract code example for pattern."""
        # Return first 500 characters containing pattern
        signatures = self.pattern_signatures.get(pattern_name, [])
        for sig in signatures:
            if sig in content:
                start = content.find(sig)
                return content[max(0, start - 100) : start + 400]
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

    def _extract_pattern_code_from_signatures(self, content: str, signatures: list[str]) -> str:
        """Extract code example for pattern from signatures."""
        # Return first 500 characters containing any signature
        for sig in signatures:
            if sig in content:
                start = content.find(sig)
                return content[max(0, start - 100) : start + 400]
        return ""

    def _get_domain_pattern_description(self, subagent_type: str, pattern_name: str) -> str:
        """Get description for domain-specific pattern."""
        descriptions = {
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
