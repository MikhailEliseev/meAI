"""
Competitive Intel Agents — production agent implementations.

IMPORT HYGIENE RULES (enforced by code review, auto-checked in CI):
1. NO `import random` in any CI agent — use structured null (confidence=0.0, data_source="unavailable")
2. Prefer api_clients/ over raw `import httpx` — api_clients/base.py provides circuit breaker,
   retry with exponential backoff, rate limiting, and response caching.
   New agents MUST use api_clients/. Existing agents should migrate incrementally.
3. All API-gated agents MUST return structured null when API key is absent.
"""

# Lint guard: NO random in CI agents.
# Structured null (confidence=0.0) is the correct pattern for unavailable data,
# not random generation or hardcoded mock values.
import sys as _sys
import os as _os

if _os.path.basename(_sys.argv[0]) not in ("pytest", "py.test"):
    _this_dir = _os.path.dirname(_os.path.abspath(__file__))
    for _fname in sorted(_os.listdir(_this_dir)):
        if _fname.endswith(".py") and _fname != "__init__.py":
            _fpath = _os.path.join(_this_dir, _fname)
            with open(_fpath, encoding="utf-8") as _f:
                _content = _f.read()
            if "import random" in _content or "from random" in _content:
                _msg = (
                    f"ERROR: {_fname} imports random. "
                    f"Use structured null pattern (confidence=0.0) instead."
                )
                raise ImportError(_msg)

# CI CHECK (run in CI pipeline, not at import time):
# grep -rn "import random\|from random" AIM/src/aim/subagents/competitive_intel/agents/*.py \
#   | grep -v __pycache__ | grep -v ".pyc" \
#   && echo "FAIL: random import found" && exit 1
