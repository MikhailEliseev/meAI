"""run_lighthouse — Hermes tool: Self-hosted website performance audit via Lighthouse CLI.

No Google API dependency. Runs local Lighthouse (same engine as PageSpeed Insights)
via headless Chromium. Returns Core Web Vitals, performance scores, and diagnostics.
"""

import asyncio
import json
import logging
import os
import shutil
import signal
import tempfile

from tools.registry import registry

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────

def _find_chromium() -> str:
    """Find Chromium binary, preferring Playwright's bundled version."""
    explicit = os.getenv("LIGHTHOUSE_CHROMIUM_PATH", "")
    if explicit and os.path.exists(explicit):
        return explicit
    playwright_dir = os.path.expanduser("~/.cache/ms-playwright")
    if os.path.isdir(playwright_dir):
        for entry in sorted(os.listdir(playwright_dir), reverse=True):
            chrome_path = os.path.join(playwright_dir, entry, "chrome-linux64", "chrome")
            if os.path.isfile(chrome_path):
                return chrome_path
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return ""

_CHROMIUM_PATH = _find_chromium()
_LIGHTHOUSE_BIN = shutil.which("lighthouse") or "/usr/local/bin/lighthouse"

# ── Timeout (shorter — we kill stuck processes in a separate thread) ──────
_LH_TIMEOUT = 45  # seconds
_LH_MAX_WAIT_FOR_LOAD = 25000  # ms — page load deadline


def _parse_lighthouse_result(raw_json: dict) -> dict:
    """Extract key metrics from Lighthouse JSON report."""
    result: dict = {
        "url": raw_json.get("requestedUrl", raw_json.get("finalUrl", "")),
        "version": raw_json.get("lighthouseVersion", ""),
        "scores": {},
        "metrics": {},
        "audits_summary": {},
    }

    # Categories (0-1 → 0-100)
    categories = raw_json.get("categories", {})
    for cat_id, cat_data in categories.items():
        score = cat_data.get("score")
        if score is not None:
            result["scores"][cat_id] = round(score * 100)

    # If no category scores, try the top-level score
    perf_score = raw_json.get("score")  # some LH versions put it here

    # Core Web Vitals from audits
    audits = raw_json.get("audits", {})

    metric_map = {
        "largest-contentful-paint": ("lcp_ms", lambda v: round(v.get("numericValue", 0))),
        "first-contentful-paint": ("fcp_ms", lambda v: round(v.get("numericValue", 0))),
        "total-blocking-time": ("tbt_ms", lambda v: round(v.get("numericValue", 0))),
        "cumulative-layout-shift": ("cls", lambda v: round(v.get("numericValue", 0), 3)),
        "speed-index": ("si_ms", lambda v: round(v.get("numericValue", 0))),
        "interactive": ("tti_ms", lambda v: round(v.get("numericValue", 0))),
        "server-response-time": ("ttfb_ms", lambda v: round(v.get("numericValue", 0))),
    }

    for audit_id, (key_name, formatter) in metric_map.items():
        audit = audits.get(audit_id, {})
        if audit and audit.get("numericValue") is not None:
            result["metrics"][key_name] = formatter(audit)

    # Human-readable display values
    display_map = {
        "largest-contentful-paint": "lcp_display",
        "first-contentful-paint": "fcp_display",
        "total-blocking-time": "tbt_display",
        "cumulative-layout-shift": "cls_display",
        "speed-index": "si_display",
    }
    for audit_id, display_key in display_map.items():
        audit = audits.get(audit_id, {})
        if audit and audit.get("displayValue"):
            result["metrics"][display_key] = audit.get("displayValue")

    # Overall assessment
    perf = result["scores"].get("performance")
    if perf is None and perf_score is not None:
        perf = round(perf_score * 100) if isinstance(perf_score, float) and perf_score <= 1 else perf_score
    if perf is not None:
        if perf >= 90:
            result["assessment"] = "good"
        elif perf >= 50:
            result["assessment"] = "needs_improvement"
        else:
            result["assessment"] = "poor"

    # Key diagnostics
    diagnostic_audits = {
        "render-blocking-resources": "render_blocking",
        "unused-css-rules": "unused_css",
        "unused-javascript": "unused_js",
        "uses-responsive-images": "responsive_images",
        "uses-optimized-images": "optimized_images",
        "uses-text-compression": "text_compression",
        "modern-image-formats": "modern_images",
    }
    for audit_id, key in diagnostic_audits.items():
        audit = audits.get(audit_id, {})
        if audit:
            result["audits_summary"][key] = {
                "score": audit.get("score"),
                "displayValue": audit.get("displayValue", ""),
            }

    return result


async def handle_run_lighthouse(url: str = None, **kwargs) -> str:
    """Run Lighthouse audit on a URL."""
    if isinstance(url, dict):
        url = url.get("url", "")

    if not url:
        return json.dumps({"error": "url is required"}, ensure_ascii=False)

    if not url.startswith("http"):
        url = "https://" + url

    logger.info("Running Lighthouse for: %s", url)

    result = await _run_single_lighthouse(url)
    if result and "error" not in result:
        result["source"] = "lighthouse_cli"
        return json.dumps(result, ensure_ascii=False)

    return json.dumps({
        "error": "Lighthouse audit failed",
        "detail": str(result.get("detail", "")) if result else "no result",
    }, ensure_ascii=False)


async def _run_single_lighthouse(url: str) -> dict | None:
    """Run Lighthouse with timeout and proper process cleanup."""
    output_path = None
    proc = None

    try:
        fd, output_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)

        chrome_flags = [
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-software-rasterizer",
        ]

        cmd = [
            _LIGHTHOUSE_BIN,
            url,
            "--preset=desktop",
            "--output=json",
            f"--output-path={output_path}",
            "--quiet",
            "--no-enable-error-reporting",
            f"--max-wait-for-load={_LH_MAX_WAIT_FOR_LOAD}",
            "--chrome-flags=" + " ".join(chrome_flags),
        ]

        env = os.environ.copy()
        if _CHROMIUM_PATH:
            env["CHROME_PATH"] = _CHROMIUM_PATH

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid,  # create new process group
        )

        try:
            _, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=_LH_TIMEOUT,
            )
        except asyncio.TimeoutError:
            # Kill the entire process group
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            logger.warning("Lighthouse timeout (%ss) for %s — killed process group", _LH_TIMEOUT, url)
            return {"error": "timeout", "detail": f"Audit exceeded {_LH_TIMEOUT}s"}

        if proc.returncode != 0:
            stderr_text = stderr.decode("utf-8", errors="replace")[:300] if stderr else "no stderr"
            logger.warning("Lighthouse exit %d for %s: %s", proc.returncode, url, stderr_text)
            return {"error": f"Lighthouse exited with code {proc.returncode}", "detail": stderr_text}

        # Read JSON output
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to parse Lighthouse JSON: %s", e)
            return {"error": "Failed to parse result"}

        parsed = _parse_lighthouse_result(data)

        logger.info(
            "Lighthouse done: perf=%s lcp=%s tbt=%s cls=%s",
            parsed.get("scores", {}).get("performance"),
            parsed.get("metrics", {}).get("lcp_display"),
            parsed.get("metrics", {}).get("tbt_display"),
            parsed.get("metrics", {}).get("cls_display"),
        )

        return parsed

    except Exception as e:
        logger.exception("Lighthouse audit failed: %s", e)
        return {"error": str(e)}

    finally:
        # Cleanup
        if proc is not None and proc.returncode is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
        if output_path:
            try:
                os.unlink(output_path)
            except OSError:
                pass


# ── Registry ──────────────────────────────────────────────────────────────
registry.register(
    name="run_lighthouse",
    toolset="aim-operations",
    schema={
            "name": "run_lighthouse",
            "description": "Аудит скорости сайта через локальный Lighthouse CLI. "
                           "НЕ использует Google API. Измеряет Core Web Vitals: "
                           "LCP, FCP, TBT, CLS, SI, TTI + performance score 0-100. "
                           "Быстрый — до 20 секунд на обычных сайтах.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL сайта для аудита (например https://arclinic.ru)",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_run_lighthouse,
    check_fn=lambda: bool(_LIGHTHOUSE_BIN and os.path.exists(_LIGHTHOUSE_BIN)),
    is_async=True,
    description="Self-hosted website performance audit — Lighthouse CLI, no Google API",
)
