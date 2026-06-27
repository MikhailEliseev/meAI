#!/usr/bin/env python3
"""v3.3.0 test harness — single-pass agent (no orchestrator, no pipeline).

Usage (inside container):
    docker exec aim-hermes python3 /opt/data/phase7/run_v330_test.py \\
        --url https://iphk.ru --slug plastic-iphk

Saves artifacts to /opt/data/memories/proposals/<slug>/{proposal.html, metadata.json}.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, "/opt/hermes")

OUTPUT_BASE = "/opt/data/memories/proposals"
TIMEOUT_SECONDS = 1800


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


async def _heartbeat(session_id, stop_event):
    elapsed = 0
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=60)
            return
        except asyncio.TimeoutError:
            pass
        elapsed += 60
        print(f"[{_iso_now()}] session={session_id} elapsed={elapsed}s", flush=True)


async def _invoke(url, slug, session_id):
    from app.agent_wrapper import run_agent
    from app.tools import register_all_tools
    register_all_tools()

    message = (
        f"Сделай полный пресейл для клиники {url}. "
        "Собери данные: prescan, финансы, врачи, SEO, отзывы, конкуренты, "
        "соцсети, реклама, цены. Создай HTML-КП через generate_html_report. "
        f"ОБЯЗАТЕЛЬНО передай session_hash='{slug}' в generate_html_report. "
        "narrative_md должен быть МИНИМУМ 20000 символов (полный отчёт в 10 секций по SOUL.md). "
        "Следуй SOUL.md — используй все доступные инструменты (минимум 10 из 14 mandatory)."
    )

    stop_event = asyncio.Event()
    hb = asyncio.create_task(_heartbeat(session_id, stop_event))
    try:
        result = await asyncio.wait_for(
            run_agent(message=message, session_id=session_id, mode="PRESALE"),
            timeout=TIMEOUT_SECONDS,
        )
        return result
    finally:
        stop_event.set()
        try:
            await asyncio.wait_for(hb, timeout=5)
        except asyncio.TimeoutError:
            hb.cancel()


def _save_metadata(args, session_id, result, duration):
    slug = args.slug
    out_dir = f"{OUTPUT_BASE}/{slug}"
    os.makedirs(out_dir, exist_ok=True)

    reply = (result or {}).get("reply", "") if isinstance(result, dict) else str(result)
    tool_calls = (result or {}).get("tool_calls", []) if isinstance(result, dict) else []

    metadata = {
        "harness_version": "v3.3.0-test",
        "session_id": session_id,
        "client_url": args.url,
        "client_slug": slug,
        "started_at": started_at,
        "completed_at": _iso_now(),
        "duration_seconds": duration,
        "reply_chars": len(reply),
        "tool_calls_count": len(tool_calls) if isinstance(tool_calls, list) else 0,
        "tool_calls": [t.get("name", "?") if isinstance(t, dict) else str(t) for t in (tool_calls or [])][:20],
    }

    with open(f"{out_dir}/metadata_v330.json", "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Also save reply as markdown for inspection
    with open(f"{out_dir}/reply_v330.md", "w") as f:
        f.write(reply)

    # Check for HTML in multiple locations (LLM may save to sessions-archive/)
    html_path = f"{out_dir}/proposal.html"
    if not os.path.exists(html_path):
        # Try sessions-archive/{slug}/report.html (generate_html_report default)
        html_path = f"/opt/data/sessions-archive/{slug}/report.html"
    if not os.path.exists(html_path):
        # Try sessions-archive/inline-*/report.html (when LLM omits session_hash)
        import glob
        candidates = sorted(
            glob.glob("/opt/data/sessions-archive/inline-*/report.html"),
            key=os.path.getmtime,
            reverse=True,
        )
        if candidates:
            html_path = candidates[0]
    if os.path.exists(html_path):
        metadata["html_report_path"] = html_path
        metadata["html_chars"] = os.path.getsize(html_path)
    else:
        metadata["html_report_path"] = ""
        metadata["html_chars"] = 0

    print(f"PHASE7_V330_RESULT slug={slug} duration={duration:.1f}s "
          f"reply_chars={len(reply)} tools={metadata['tool_calls_count']} "
          f"html_chars={metadata['html_chars']}")
    print(f"  metadata: {out_dir}/metadata_v330.json")
    print(f"  reply: {out_dir}/reply_v330.md")


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--session-id", default=None)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    started_at = _iso_now()
    session_id = args.session_id or f"v330-{args.slug}-{int(time.time())}"
    print(f"[{started_at}] START v3.3.0 slug={args.slug} url={args.url} session={session_id}")

    t0 = time.time()
    try:
        result = asyncio.run(_invoke(args.url, args.slug, session_id))
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    duration = time.time() - t0

    _save_metadata(args, session_id, result, duration)
