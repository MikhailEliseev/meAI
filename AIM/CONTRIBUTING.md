# Contributing Guidelines

Welcome to the AIM Testing Infrastructure project! This guide will help you contribute effectively.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Git Workflow](#git-workflow)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Review Process](#review-process)
- [Issue Reporting](#issue-reporting)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of async Python
- Familiarity with pytest

### Quick Start

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/meAI.git
   cd meAI
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Run Tests**
   ```bash
   cd AIM
   pytest tests/ -v
   ```

## Development Setup

### Environment Configuration

1. **Copy Environment Template**
   ```bash
   cp AIM/.env.example AIM/.env
   ```

2. **Configure API Keys** (optional for testing)
   ```bash
   # Edit AIM/.env
   SEMRUSH_API_KEY=your_key_here  # Optional
   AHREFS_API_KEY=your_key_here   # Optional
   ```

3. **Validate Setup**
   ```bash
   python AIM/scripts/validate_env.py
   ```

### IDE Setup

**VS Code:**
```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["AIM/tests"],
  "editor.formatOnSave": true
}
```

**PyCharm:**
- Enable pytest as test runner
- Configure ruff as external tool
- Enable type checking with mypy

### Pre-commit Hooks (Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Code Style

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line Length:** 100 characters (not 79)
- **Quotes:** Double quotes for strings
- **Imports:** Absolute imports preferred
- **Type Hints:** Required for all functions

### Formatting Tools

**Ruff (Linter + Formatter):**
```bash
# Check code
ruff check .

# Format code
ruff format .

# Fix auto-fixable issues
ruff check --fix .
```

**MyPy (Type Checking):**
```bash
# Check types
mypy src/
```

### Code Conventions

**1. Type Hints**
```python
# Good
async def expand_keywords(
    self,
    seed_keyword: str,
    max_keywords: int = 100
) -> list[KeywordData]:
    ...

# Bad
async def expand_keywords(self, seed_keyword, max_keywords=100):
    ...
```

**2. Docstrings**
```python
def calculate_score(keywords: list[KeywordData]) -> float:
    """Calculate overall keyword score.
    
    Args:
        keywords: List of keyword data objects
        
    Returns:
        Score between 0 and 100
        
    Raises:
        ValueError: If keywords list is empty
    """
    if not keywords:
        raise ValueError("Keywords list cannot be empty")
    return sum(kw.score for kw in keywords) / len(keywords)
```

**3. Async/Await**
```python
# Good - async all the way
async def fetch_data(self) -> dict:
    response = await self.client.get("/api/data")
    return await response.json()

# Bad - blocking in async
async def fetch_data(self) -> dict:
    response = requests.get("/api/data")  # Blocking!
    return response.json()
```

**4. Error Handling**
```python
# Good - specific exceptions
try:
    result = await api_call()
except httpx.TimeoutException:
    logger.warning("API timeout, using fallback")
    result = fallback_data()
except httpx.HTTPStatusError as e:
    logger.error(f"API error: {e.response.status_code}")
    raise

# Bad - bare except
try:
    result = await api_call()
except:  # Too broad!
    result = None
```

**5. Logging**
```python
import structlog

logger = structlog.get_logger()

# Good - structured logging
logger.info(
    "keyword_expansion_complete",
    seed=seed_keyword,
    count=len(keywords),
    duration_ms=duration
)

# Bad - string formatting
logger.info(f"Expanded {seed_keyword} to {len(keywords)} keywords")
```

## Git Workflow

### Branch Naming

- `feat/<feature-name>` - New features
- `fix/<bug-name>` - Bug fixes
- `docs/<doc-name>` - Documentation
- `test/<test-name>` - Test additions
- `refactor/<refactor-name>` - Code refactoring

**Examples:**
- `feat/keyword-clustering`
- `fix/rate-limiter-bug`
- `docs/api-integration-guide`

### Commit Messages

Follow **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `test` - Tests
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `chore` - Maintenance

**Examples:**
```
feat(keyword-research): add clustering algorithm

Implement similarity-based keyword clustering using TF-IDF
and cosine similarity. Groups keywords into semantic clusters
for better organization.

Closes #123
```

```
fix(rate-limiter): prevent token overflow

Token bucket was allowing more than capacity tokens to accumulate.
Added max() check to cap tokens at capacity.

Fixes #456
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run Tests Locally**
   ```bash
   cd AIM
   pytest tests/ -v
   ruff check .
   mypy src/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

5. **Push to Fork**
   ```bash
   git push origin feat/my-feature
   ```

6. **Create Pull Request**
   - Use PR template
   - Link related issues
   - Add screenshots if UI changes
   - Request review

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## Testing Requirements

### Test Coverage Rules

1. **All New Code Must Have Tests**
   - Minimum 80% coverage for new code
   - 100% coverage for critical paths

2. **Test Types Required**
   - Unit tests for all functions/methods
   - Integration tests for component interactions
   - E2E tests for complete workflows

3. **Test Quality**
   - Tests must be deterministic
   - No flaky tests allowed
   - Clear test names and assertions

### Writing Tests

**1. Test File Location**
```
src/aim/subagents/keyword_research.py
→ tests/unit/test_keyword_research.py
```

**2. Test Structure**
```python
import pytest
from aim.subagents.keyword_research import KeywordResearchAgent

class TestKeywordResearchAgent:
    """Test suite for Keyword Research Agent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return KeywordResearchAgent(api_key="test")
    
    async def test_expand_keywords_success(self, agent):
        """Test successful keyword expansion."""
        # Arrange
        seed = "dental implants"
        
        # Act
        keywords = await agent.expand_keywords(seed, max_keywords=10)
        
        # Assert
        assert len(keywords) == 10
        assert all(kw.volume > 0 for kw in keywords)
    
    async def test_expand_keywords_empty_seed(self, agent):
        """Test error handling for empty seed."""
        with pytest.raises(ValueError, match="Seed keyword cannot be empty"):
            await agent.expand_keywords("", max_keywords=10)
```

**3. Mock External Dependencies**
```python
@pytest.fixture
def mock_semrush_client(monkeypatch):
    """Mock SEMrush API client."""
    async def mock_expand(*args, **kwargs):
        return [
            KeywordData(keyword="test", volume=1000, cpc=5.0)
        ]
    
    monkeypatch.setattr(
        "aim.subagents.api_clients.semrush.SEMrushClient.expand_keywords",
        mock_expand
    )
```

### Running Tests Before PR

```bash
# Run all tests
cd AIM
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/aim --cov-report=term-missing

# Check coverage threshold
pytest tests/ --cov=src/aim --cov-fail-under=80

# Run linter
ruff check .

# Run type checker
mypy src/
```

## Documentation

### Documentation Requirements

1. **Code Documentation**
   - Docstrings for all public functions/classes
   - Type hints for all parameters and returns
   - Examples in docstrings for complex functions

2. **README Updates**
   - Update README.md if adding new features
   - Add usage examples
   - Update installation instructions if needed

3. **API Documentation**
   - Document all API integrations
   - Include authentication steps
   - Provide example requests/responses

### Documentation Style

**Module Docstring:**
```python
"""Keyword Research Agent.

This module provides functionality for keyword research using SEMrush
and Ahrefs APIs. It includes keyword expansion, clustering, and
priority scoring.

Example:
    >>> agent = KeywordResearchAgent(api_key="...")
    >>> keywords = await agent.expand_keywords("dental implants")
    >>> print(len(keywords))
    100
"""
```

**Function Docstring:**
```python
async def expand_keywords(
    self,
    seed_keyword: str,
    max_keywords: int = 100,
    min_volume: int = 10
) -> list[KeywordData]:
    """Expand seed keyword into related keywords.
    
    Uses SEMrush API to find related keywords based on the seed.
    Filters by minimum search volume and sorts by relevance.
    
    Args:
        seed_keyword: Starting keyword for expansion
        max_keywords: Maximum number of keywords to return
        min_volume: Minimum monthly search volume
        
    Returns:
        List of keyword data objects sorted by relevance
        
    Raises:
        ValueError: If seed_keyword is empty
        APIError: If API request fails
        
    Example:
        >>> keywords = await agent.expand_keywords(
        ...     "dental implants",
        ...     max_keywords=50,
        ...     min_volume=100
        ... )
        >>> len(keywords)
        50
    """
```

## Review Process

### Code Review Guidelines

**For Authors:**
1. Self-review before requesting review
2. Ensure all tests pass
3. Update documentation
4. Respond to feedback promptly
5. Keep PRs focused and small

**For Reviewers:**
1. Review within 24 hours
2. Be constructive and specific
3. Test the changes locally
4. Check for edge cases
5. Approve when satisfied

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Error handling is robust
- [ ] Logging is appropriate

### Approval Process

1. **One Approval Required** for minor changes
2. **Two Approvals Required** for major changes
3. **All Tests Must Pass** in CI
4. **No Merge Conflicts** with main branch

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen

**Actual behavior**
What actually happened

**Environment**
- OS: [e.g., macOS 13.0]
- Python: [e.g., 3.11.5]
- Version: [e.g., 1.0.0]

**Additional context**
Any other relevant information
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other solutions you've thought about

**Additional context**
Any other relevant information
```

### Security Issues

**Do not open public issues for security vulnerabilities.**

Email security issues to: security@iamaim.ru

## Getting Help

- **Documentation:** Check docs/ directory
- **Issues:** Search existing issues first
- **Discussions:** Use GitHub Discussions for questions
- **Email:** contact@iamaim.ru

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions
- Follow project guidelines

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

**Thank you for contributing to AIM Testing Infrastructure!**

**Last Updated:** 2026-05-15  
**Version:** 1.0  
**Maintainer:** Mikhail Eliseev
