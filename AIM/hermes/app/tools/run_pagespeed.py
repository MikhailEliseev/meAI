"""run_pagespeed — Hermes tool: Lighthouse Performance Audit.

Uses Google Lighthouse (Node.js CLI) with headless Chromium
to measure Core Web Vitals: Performance score, LCP, FCP, TBT, CLS.
"""

import asyncio
import json
import logging
import os
import subprocess
import time

from app.tools._url_utils import recover_url_from_context
from tools.registry import registry

logger = logging.getLogger(__name__)

# Chromium from Playwright installation
_CHROME_PATH = os.path.expanduser(
    os.getenv("CHROME_PATH", "~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome")
)
_LIGHTHOUSE_TIMEOUT = 120  # seconds — Lighthouse can be slow


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def _run_lighthouse(url: str) -> dict:
    """Run Lighthouse CLI and return parsed performance results."""
    chrome_path = os.path.expanduser(_CHROME_PATH)
    if not os.path.exists(chrome_path):
        # Try to find chromium automatically
        import glob
        candidates = glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome"))
        if candidates:
            chrome_path = candidates[0]
        else:
            return {"error": "Chromium not found", "detail": f"Tried: {_CHROME_PATH}"}

    flags = "--headless --no-sandbox --disable-gpu --disable-dev-shm-usage"
    
    cmd = [
        "lighthouse", url,
        "--output=json",
        f"--chrome-flags={flags}",
        "--only-categories=performance",
        "--quiet",
    ]
    
    env = {**os.environ, "CHROME_PATH": chrome_path}
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=_LIGHTHOUSE_TIMEOUT
        )
        
        if proc.returncode != 0:
            error_msg = stderr.decode()[:500] if stderr else f"exit code {proc.returncode}"
            logger.error("Lighthouse failed for %s: %s", url, error_msg)
            return {"error": "Lighthouse audit failed", "detail": error_msg}
        
        data = json.loads(stdout)
        
        # Extract key metrics
        categories = data.get("categories", {})
        perf = categories.get("performance", {})
        score = int((perf.get("score") or 0) * 100)
        
        audits = data.get("audits", {})
        
        def _get_audit(audit_id: str) -> dict | None:
            a = audits.get(audit_id, {})
            if not a:
                return None
            return {
                "displayValue": a.get("displayValue", ""),
                "numericValue": a.get("numericValue"),
                "score": int((a.get("score") or 0) * 100),
            }
        
        # Core Web Vitals
        lcp = _get_audit("largest-contentful-paint")
        fcp = _get_audit("first-contentful-paint")
        tbt = _get_audit("total-blocking-time")
        cls = _get_audit("cumulative-layout-shift")
        si = _get_audit("speed-index")
        tti = _get_audit("interactive")
        
        # Distribution (CrUX-like: good / needs improvement / poor)
        lcp_dist = {}
        fcp_dist = {}
        tbt_dist = {}
        cls_dist = {}
        for audit_id, dist_dict in [
            ("largest-contentful-paint", lcp_dist),
            ("first-contentful-paint", fcp_dist),
            ("total-blocking-time", tbt_dist),
            ("cumulative-layout-shift", cls_dist),
        ]:
            a = audits.get(audit_id, {})
            if a:
                dist_dict["good"] = a.get("displayValue", "")
        
        result = {
            "url": url,
            "performance_score": score,
            "method": "Lighthouse",
            "lcp": lcp.get("displayValue", "—") if lcp else "—",
            "lcp_seconds": lcp.get("numericValue", 0) / 1000 if lcp and lcp.get("numericValue") else None,
            "fcp": fcp.get("displayValue", "—") if fcp else "—",
            "fcp_seconds": fcp.get("numericValue", 0) / 1000 if fcp and fcp.get("numericValue") else None,
            "tbt": tbt.get("displayValue", "—") if tbt else "—",
            "tbt_ms": int(tbt.get("numericValue", 0)) if tbt and tbt.get("numericValue") else None,
            "cls": cls.get("displayValue", "—") if cls else "—",
            "cls_value": cls.get("numericValue") if cls else None,
            "si": si.get("displayValue", "—") if si else "—",
            "si_seconds": si.get("numericValue", 0) / 1000 if si and si.get("numericValue") else None,
            "tti": tti.get("displayValue", "—") if tti else "—",
            "tti_seconds": tti.get("numericValue", 0) / 1000 if tti and tti.get("numericValue") else None,
            "analyzed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        
        return result
        
    except asyncio.TimeoutError:
        logger.error("Lighthouse timed out for %s after %ds", url, _LIGHTHOUSE_TIMEOUT)
        return {"error": f"Lighthouse timed out after {_LIGHTHOUSE_TIMEOUT}s", "url": url}
    except json.JSONDecodeError as e:
        logger.error("Lighthouse JSON parse error for %s: %s", url, e)
        return {"error": "Lighthouse output parse error", "detail": str(e)}
    except Exception as e:
        logger.exception("Lighthouse unexpected error for %s", url)
        return {"error": "Lighthouse unexpected error", "detail": str(e)}


async def handle_run_pagespeed(url=None, **kwargs) -> str:
    """Run Lighthouse performance audit on a website.

    Args:
        url: Website URL to analyze.

    Returns:
        JSON with performance score and Core Web Vitals.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]

    if not url:
        session_id_local = kwargs.get("session_id", "") or os.getenv("PIPELINE_SESSION_ID", "")
        recovered = recover_url_from_context(session_id_local, kwargs)
        if recovered:
            url = recovered
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            logger.info("run_pagespeed: URL recovered via fallback: %s", url)
    if not url:
        return json.dumps({"error": "URL is required"}, ensure_ascii=False)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("Running Lighthouse for: %s", url)

    try:
        from app.main import push_tool_progress
        push_tool_progress("pagespeed", f"🚀 Lighthouse: замеряю скорость {url}…")
    except Exception:
        pass

    result = await _run_lighthouse(url)
    
    try:
        from app.main import push_tool_progress
        if "error" in result:
            push_tool_progress("pagespeed", f"⚠️ Lighthouse: {result.get('error', 'unknown error')}")
        else:
            push_tool_progress("pagespeed", f"✅ Lighthouse: {result.get('performance_score', '?')}/100")
    except Exception:
        pass

    return json.dumps(result, ensure_ascii=False, indent=2)


registry.register(
    name="run_pagespeed",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_pagespeed",
            "description": (
                "Запустить Lighthouse-аудит скорости сайта. "
                "Использует Google Lighthouse с headless Chromium. "
                "Возвращает Performance score и Core Web Vitals (LCP, FCP, TBT, CLS)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL сайта для аудита",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_pagespeed,
    check_fn=lambda: True,
    is_async=True,
    description="Запустить Lighthouse-аудит скорости сайта",
    emoji="🚀",
)
