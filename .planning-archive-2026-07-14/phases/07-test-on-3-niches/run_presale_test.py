#!/usr/bin/env python3
"""Phase 7 Test Harness — invoke 3-pass orchestrator for niche tests.

Usage (inside container):
    docker exec -e ORCHESTRATOR_MODE=1 aim-hermes python3 /opt/data/phase7/run_presale_test.py \\
        --url <clinic-url> --slug <client-slug> --mode PRESALE --niche plastic_surgery

Saves artifacts to /opt/data/memories/proposals/<slug>/{proposal.html, metadata.json}.
Exit codes: 0=SUCCESS, 1=FAILED (exception), 2=TIMEOUT (30 min exceeded).

Python 3.11 compatible — no f-string backslash escapes in expression parts.
"""
# IMPORTANT: set ORCHESTRATOR_MODE env BEFORE any app.* import.
import os
os.environ["ORCHESTRATOR_MODE"] = "1"

import argparse
import asyncio
import json
import sys
import time
import traceback
from datetime import datetime, timezone

sys.path.insert(0, "/opt/hermes")

OUTPUT_BASE = "/opt/data/memories/proposals"
HARNESS_VERSION = "07-01.1"
TIMEOUT_SECONDS = 1800
PROGRESS_INTERVAL = 60


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


def _parse_args():
    p = argparse.ArgumentParser(description="Phase 7 presale test harness")
    p.add_argument("--url", required=True, help="Clinic URL to scan")
    p.add_argument("--slug", required=True, help="Client slug (names output dir)")
    p.add_argument("--mode", default="PRESALE", choices=["PRESALE", "ADMIN"],
                   help="Orchestrator mode prompt (default PRESALE)")
    p.add_argument("--niche", default="unknown",
                   choices=["plastic_surgery", "dental", "cosmetology", "unknown"],
                   help="Niche tag recorded in metadata")
    p.add_argument("--session-id", default=None,
                   help="Override session id (default phase7-<slug>-<timestamp>)")
    return p.parse_args()


async def _heartbeat(session_id, stop_event):
    """Emit heartbeat to stdout every 60s. Live pass_status unavailable —
    run_three_pass does not stream intermediate state."""
    elapsed = 0
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=PROGRESS_INTERVAL)
            return
        except asyncio.TimeoutError:
            pass
        elapsed += PROGRESS_INTERVAL
        msg = "[" + _iso_now() + "] session=" + session_id + " pass_status=_running elapsed=" + str(elapsed) + "s"
        print(msg, flush=True)


async def _invoke(args, session_id):
    from app.orchestrator.three_pass import run_three_pass
    # CRITICAL: register all Hermes tools before creating AIAgent — without this
    # the tool registry stays empty (0 tools) and LLM has nothing to call.
    from app.tools import register_all_tools
    register_all_tools()
    stop_event = asyncio.Event()
    hb = asyncio.create_task(_heartbeat(session_id, stop_event))
    try:
        state = await asyncio.wait_for(
            run_three_pass(session_id=session_id, client_url=args.url,
                           client_name=args.slug, mode=args.mode),
            timeout=TIMEOUT_SECONDS,
        )
        return state
    finally:
        stop_event.set()
        try:
            await asyncio.wait_for(hb, timeout=5)
        except asyncio.TimeoutError:
            hb.cancel()


def _summarize_gap(gap_report):
    if not gap_report:
        return None
    if not isinstance(gap_report, dict):
        return {"_raw": str(gap_report)[:500]}
    keys = ("coverage", "coverage_pct", "covered_pct", "status", "pass",
            "filled_items", "missing_items", "not_applicable_items",
            "partial_items", "total_items")
    summary = {k: gap_report[k] for k in keys if k in gap_report}
    return summary or {"_raw_keys": list(gap_report.keys())[:20]}


def _save_html(output_dir, state):
    """Copy HTML from state path or fallback into proposal.html. Returns (target, chars, src)."""
    target = os.path.join(output_dir, "proposal.html")
    src = (state.html_report_path or "").strip()
    candidates = []
    if src:
        candidates.append(src)
    candidates.append("/opt/data/sessions-archive/" + state.session_id + "/report.html")
    for path in candidates:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
            with open(target, "w", encoding="utf-8") as f:
                f.write(html)
            return target, len(html), path
    return "", 0, src


async def main():
    args = _parse_args()
    session_id = args.session_id or ("phase7-" + args.slug + "-" +
                                     datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    output_dir = os.path.join(OUTPUT_BASE, args.slug)
    os.makedirs(output_dir, exist_ok=True)

    started_at = _iso_now()
    t0 = time.time()
    print("[" + started_at + "] START slug=" + args.slug + " url=" + args.url +
          " mode=" + args.mode + " niche=" + args.niche + " session=" + session_id, flush=True)

    status = "SUCCESS"
    error_msg = ""
    traceback_str = ""
    state = None
    try:
        state = await _invoke(args, session_id)
    except asyncio.TimeoutError:
        status = "TIMEOUT"
        error_msg = "Exceeded " + str(TIMEOUT_SECONDS) + "s timeout"
    except Exception as e:
        status = "FAILED"
        error_msg = type(e).__name__ + ": " + str(e)
        traceback_str = traceback.format_exc()

    completed_at = _iso_now()
    duration = round(time.time() - t0, 1)

    meta = {
        "harness_version": HARNESS_VERSION,
        "status": status,
        "session_id": session_id,
        "client_url": args.url,
        "client_slug": args.slug,
        "mode": args.mode,
        "niche_tag": args.niche,
        "orchestrator_mode_env": os.environ.get("ORCHESTRATOR_MODE", ""),
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": duration,
        "timeout_seconds": TIMEOUT_SECONDS,
        "orchestrator_state": None,
    }

    if state is not None:
        html_target, html_chars, html_src = _save_html(output_dir, state)
        meta["orchestrator_state"] = {
            "pass_status": state.pass_status,
            "niche_detected": state.niche,
            "html_report_path": state.html_report_path,
            "error_message": state.error_message,
            "gap_report_summary": _summarize_gap(state.gap_report),
        }
        meta["proposal_html_saved_to"] = html_target
        meta["proposal_html_chars"] = html_chars
        meta["proposal_html_source"] = html_src

    if error_msg:
        meta["error"] = error_msg
    if traceback_str:
        meta["traceback"] = traceback_str

    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, default=str)

    html_for_print = meta.get("proposal_html_saved_to", "") or "(none)"
    print("[" + completed_at + "] PHASE7_RESULT slug=" + args.slug +
          " status=" + status + " html_path=" + html_for_print +
          " duration=" + str(duration), flush=True)
    print("  metadata: " + metadata_path, flush=True)

    if status == "TIMEOUT":
        sys.exit(2)
    if status == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
