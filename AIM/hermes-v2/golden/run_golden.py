#!/usr/bin/env python3
"""Golden-тесты качества ответов чата AIM.

Паттерн snapshot (run-once / assert-many):
  --refresh   прогон через РЕАЛЬНЫЕ API → snapshot.json + transcript.md
  (без флага)  проверки G1-G5 на существующих snapshot → scorecard

Исполнение: внутри контейнера aim-hermes-v2 (docker exec), где все ключи в env.
Публикация отчёта в WP по умолчанию ОТКЛЮЧЕНА (GOLDEN_SKIP_PUBLISH=1),
чтобы не загрязнять прод. Обезвреживается monkeypatch-ем _auto_publish_report.

Usage (в контейнере, workdir=/opt/hermes-v2):
  python3 golden/run_golden.py --refresh              # все кейсы, реальный прогон
  python3 golden/run_golden.py --refresh --case dentakrd
  python3 golden/run_golden.py                        # проверить snapshot
  python3 golden/run_golden.py --refresh --judge      # + LLM-as-judge
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime, timezone

# ── path bootstrap: родитель (где лежит app/) ──
_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_ROOT = os.path.dirname(_HERE)
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

CASES_FILE = os.path.join(_HERE, "cases.json")
DEFAULT_OUT = os.environ.get("GOLDEN_OUT", os.path.join(_HERE, "cases"))


# ────────────────────────────────────────────────────────────────────
# Загрузка кейсов
# ────────────────────────────────────────────────────────────────────

def load_cases(only: str | None = None) -> list[dict]:
    with open(CASES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    cases = data["cases"]
    if only:
        cases = [c for c in cases if c["id"] == only]
        if not cases:
            sys.exit(f"case '{only}' not found in {CASES_FILE}")
    return cases


# ────────────────────────────────────────────────────────────────────
# Monkeypatch: отключить публикацию отчёта в WordPress
# ────────────────────────────────────────────────────────────────────

def setup_environment():
    """Подготовка окружения: регистрируем тулы (как при startup) +
    опц. отключаем публикацию отчёта в WP. Без register_all() LLM
    получит пустой список тулов и не сможет их вызвать."""
    # 1. Регистрация тулов — КРИТИЧНО. Без неё get_openai_tools() = [].
    try:
        from app.tools import register_all
        register_all()
        from app.tools.registry import list_tool_names
        names = list_tool_names()
        print(f"[golden] registered {len(names)} tools: {names}")
    except Exception as e:
        print(f"[golden] WARNING: register_all failed: {e}")

    # 2. Отключить публикацию отчёта в WordPress (monkeypatch).
    if os.environ.get("GOLDEN_SKIP_PUBLISH", "1") != "1":
        return
    try:
        import app.llm as _llm  # noqa
    except Exception:
        return

    async def _noop_publish(*args, **kwargs):
        return
        yield  # noqa — делает функцию async generator

    _llm._auto_publish_report = _noop_publish
    print("[golden] WP publish DISABLED (GOLDEN_SKIP_PUBLISH=1)")


# ────────────────────────────────────────────────────────────────────
# Прогон одного кейса через реальный chat_with_tools
# ────────────────────────────────────────────────────────────────────

async def run_case(case: dict) -> dict:
    from app.llm import chat_with_tools

    url = case["url"]
    history = [{"role": "user", "content": url}]

    events = {
        "input_url": url,
        "tool_calls": [],
        "formatted_blocks": [],
        "llm_text_parts": [],
        "report": None,
        "report_title": None,
        "errors": [],
    }

    try:
        async for ev in chat_with_tools(history):
            kind = ev[0]
            if kind == "formatted":
                events["formatted_blocks"].append(ev[1])
            elif kind == "text":
                events["llm_text_parts"].append(ev[1])
            elif kind == "tool_start":
                tc = {"tool": ev[1], "args": ev[2] if len(ev) > 2 else None, "status": "start"}
                events["tool_calls"].append(tc)
            elif kind == "tool_result":
                # обновим последний start этого тула
                name = ev[1]
                result = ev[2] if len(ev) > 2 else None
                for tc in reversed(events["tool_calls"]):
                    if tc["tool"] == name and tc["status"] == "start":
                        tc["status"] = "done"
                        tc["result"] = result
                        break
            elif kind == "report_ready":
                events["report"] = ev[1] if len(ev) > 1 else None
                events["report_title"] = ev[2] if len(ev) > 2 else None
            elif kind == "finish":
                break
    except Exception as e:
        events["errors"].append(f"{type(e).__name__}: {e}")
        traceback.print_exc()

    events["llm_text"] = "".join(events.pop("llm_text_parts"))
    return events


# ────────────────────────────────────────────────────────────────────
# Snapshot I/O
# ────────────────────────────────────────────────────────────────────

def case_dir(case_id: str, out: str) -> str:
    d = os.path.join(out, case_id)
    os.makedirs(d, exist_ok=True)
    return d


def save_snapshot(case: dict, events: dict, out: str, model: str) -> dict:
    snapshot = {
        "case_id": case["id"],
        "input": {"message": case["url"]},
        "profile": case.get("profile", ""),
        "notes": case.get("notes", ""),
        "model": model,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "skip_publish": os.environ.get("GOLDEN_SKIP_PUBLISH", "1") == "1",
        "events": events,
    }
    d = case_dir(case["id"], out)
    with open(os.path.join(d, "snapshot.json"), "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    _save_transcript(snapshot, d)
    return snapshot


def _save_transcript(snapshot: dict, d: str) -> None:
    """Человекочитаемый транскрипт — для глаз."""
    ev = snapshot["events"]
    lines = [
        f"# Golden case: {snapshot['case_id']}",
        f"- URL: {snapshot['input']['message']}",
        f"- Profile: {snapshot.get('profile','')}",
        f"- Model: {snapshot['model']}",
        f"- Ran: {snapshot['ran_at']}",
        f"- Publish skipped: {snapshot['skip_publish']}",
        "",
        "## Tool calls",
    ]
    for tc in ev.get("tool_calls", []):
        ok = "✅" if tc.get("status") == "done" and not _is_err(tc.get("result")) else "⚠️"
        lines.append(f"- {ok} `{tc.get('tool')}` — {tc.get('status')}")
    if ev.get("report"):
        lines += ["", f"## Report (would publish): {ev['report']}"]
    if ev.get("errors"):
        lines += ["", "## ⚠️ Errors"] + [f"- {e}" for e in ev["errors"]]
    lines += ["", "## ── Formatted data blocks (показаны пользователю) ──", ""]
    lines.append("\n".join(ev.get("formatted_blocks", [])))
    lines += ["", "## ── LLM narrative answer ──", ""]
    lines.append(ev.get("llm_text", "(пусто)"))
    with open(os.path.join(d, "transcript.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _is_err(result) -> bool:
    if not result:
        return True
    return "error" in str(result).lower()[:60]


def load_snapshot(case_id: str, out: str) -> dict | None:
    path = os.path.join(out, case_id, "snapshot.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ────────────────────────────────────────────────────────────────────
# Scorecard
# ────────────────────────────────────────────────────────────────────

def grade(snapshot: dict) -> dict:
    from checks import run_all
    return run_all(snapshot)


def print_scorecard(results: list[tuple[str, dict, dict | None]]) -> None:
    """results: [(case_id, checks, judge_or_none)]"""
    print("\n" + "=" * 100)
    print(f"{'CASE':<14} {'G1':<11} {'G6':<11} {'G2':<8} {'G3':<6} {'G4':<7} {'G5':<5} {'G7':<5} {'JUDGE':<6}")
    print("-" * 100)
    sums = {"g1": [], "g6": [], "judge": []}
    g3_pass = 0
    g7_fail_cases = []
    for case_id, ch, jg in results:
        g1 = ch["G1_grounding"]
        g6 = ch["G6_coverage"]
        g2 = ch["G2_structure"]
        g3 = ch["G3_clean"]
        g4 = ch["G4_data"]
        g5 = ch["G5_coherence"]
        g7 = ch.get("G7_consistency", {"pass": True, "contradictions": []})
        g1m = "✅" if g1["pass"] else ("❌" if g1["score_pct"] < 30 else "⚠️")
        g6m = "✅" if g6["pass"] else ("❌" if g6["score_pct"] < 30 else "⚠️")
        g2m = "✅" if g2["pass"] else "⚠️"
        g3m = "✅" if g3["pass"] else "❌"
        g4m = "✅" if g4["pass"] else ("⚠️" if g4["score"] != "0/3" else "❌")
        g5m = "✅" if g5["pass"] else "❌"
        g7m = "✅" if g7["pass"] else "❌"
        if not g7["pass"]:
            g7_fail_cases.append((case_id, g7.get("contradictions", [])))
        jm = f"{jg['total']:.1f}" if jg and "total" in jg else "—"
        g1_str = f"{g1['score_pct']:.0f}% {g1m}"
        g6_str = f"{g6['score_pct']:.0f}% {g6m}"
        print(f"{case_id:<14} {g1_str:<11} {g6_str:<11} {g2['score']+' '+g2m:<8} {g3m:<6} {g4['score']+' '+g4m:<7} {g5m:<5} {g7m:<5} {jm:<6}")
        sums["g1"].append(g1["score_pct"])
        sums["g6"].append(g6["score_pct"])
        if g3["pass"]:
            g3_pass += 1
        if jg and "total" in jg:
            sums["judge"].append(jg["total"])

    print("-" * 100)
    n = len(results)
    avg_g1 = sum(sums["g1"]) / n if n else 0
    avg_g6 = sum(sums["g6"]) / n if n else 0
    avg_j = sum(sums["judge"]) / len(sums["judge"]) if sums["judge"] else 0
    print(f"{'AVG':<14} {f'{avg_g1:.0f}%':<11} {f'{avg_g6:.0f}%':<11} {'':<8} {f'{g3_pass}/{n}':<6} {'':<7} {'':<5} {'':<5} {f'{avg_j:.1f}' if sums['judge'] else '—':<6}")
    print("=" * 100)
    print(f"  G1 grounding (точность): {avg_g1:.0f}%  — цитируемые числа обоснованы")
    print(f"  G6 coverage  (полнота):  {avg_g6:.0f}%  — ключевые факты данных ИСПОЛЬЗОВАНЫ")
    print(f"  G3 clean pass: {g3_pass}/{n}")
    if g7_fail_cases:
        print(f"  G7 CONSISTENCY FAIL ({len(g7_fail_cases)}):")
        for cid, contra in g7_fail_cases:
            print(f"    {cid}: {contra}")
    else:
        print(f"  G7 consistency: ✅ все метрики согласованы (нет противоречий «565 vs 64»)")
    if sums["judge"]:
        print(f"  JUDGE avg: {avg_j:.1f}/5")
    print()


def print_ungrounded_details(results: list[tuple[str, dict, dict | None]]) -> None:
    """Показать конкретные неграундированные цифры — наглядное доказательство."""
    print("=" * 92)
    print("UNGROUNDED CLAIMS (цифры в ответе LLM, которых НЕТ в данных → галлюцинации):")
    print("-" * 92)
    any_ = False
    for case_id, ch, _ in results:
        g1 = ch["G1_grounding"]
        ung = g1.get("ungrounded", [])
        inn = g1.get("inn_ungrounded", [])
        if ung or inn:
            any_ = True
            nums = ", ".join(ung[:12]) if ung else "(нет чисел)"
            print(f"  {case_id}: {nums}")
            if inn:
                print(f"    ИНН не из данных: {', '.join(inn)}")
    if not any_:
        print("  (все цифры grounded — отлично)")
    print("=" * 92 + "\n")


def _print_g8_details(results: list[tuple[str, dict, dict | None]]) -> None:
    """G8: классификация ungrounded — derived (производные) vs fabricated (выдумки)."""
    print("=" * 92)
    print("G8 КЛАССИФИКАЦИЯ UNFOUNDED (derived = производные от данных, fabricated = выдумки):")
    print("-" * 92)
    any_ = False
    for case_id, ch, _ in results:
        g1 = ch["G1_grounding"]
        derived = g1.get("derived", [])
        fabricated = g1.get("fabricated", [])
        if derived or fabricated:
            any_ = True
            d = ", ".join(derived) if derived else "—"
            f = ", ".join(fabricated) if fabricated else "—"
            print(f"  {case_id}:")
            print(f"    derived (легитимно): {d}")
            print(f"    FABRICATED (выдумки): {f}")
    if not any_:
        print("  (все ungrounded обоснованы или отсутствуют)")
    print("=" * 92 + "\n")


# ────────────────────────────────────────────────────────────────────
# main
# ────────────────────────────────────────────────────────────────────

async def cmd_refresh(cases: list[dict], out: str, do_judge: bool) -> None:
    setup_environment()
    try:
        from app.config import LLM_MODEL
        model = LLM_MODEL
    except Exception:
        model = os.environ.get("LLM_MODEL", "?")
    print(f"[golden] model={model}  cases={len(cases)}  out={out}\n")

    snapshots = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']} ← {case['url']} ...", flush=True)
        events = await run_case(case)
        snap = save_snapshot(case, events, out, model)
        snapshots.append(snap)
        txt = events.get("llm_text", "")
        blk = len(events.get("formatted_blocks", []))
        err = events.get("errors", [])
        print(f"      blocks={blk}  llm_text={len(txt)} chars  tools={len(events.get('tool_calls',[]))}  errors={len(err)}")

    # пройтись чеками + опц. judge, сохранить и показать scorecard
    results = []
    for snap in snapshots:
        ch = grade(snap)
        snap["checks"] = ch
        if do_judge:
            try:
                from judge import judge_snapshot
                snap["judge"] = await judge_snapshot(snap)
            except Exception as e:
                print(f"      judge failed: {e}")
                snap["judge"] = None
        else:
            snap["judge"] = None
        # перезаписать snapshot с проверками
        d = case_dir(snap["case_id"], out)
        with open(os.path.join(d, "snapshot.json"), "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)
        results.append((snap["case_id"], ch, snap["judge"]))

    print_scorecard(results)
    print_ungrounded_details(results)


def cmd_assert(cases: list[dict], out: str) -> int:
    results = []
    missing = 0
    for case in cases:
        snap = load_snapshot(case["id"], out)
        if not snap:
            print(f"  ⚠️  нет snapshot для {case['id']} — запустите --refresh")
            missing += 1
            continue
        ch = grade(snap)
        results.append((case["id"], ch, snap.get("judge")))
    if missing == len(cases):
        print("Нет snapshot ни для одного кейса. Запустите: python3 run_golden.py --refresh")
        return 1
    print_scorecard(results)
    print_ungrounded_details(results)
    _print_g8_details(results)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="AIM golden tests")
    p.add_argument("--refresh", action="store_true", help="реальный прогон через API → snapshot")
    p.add_argument("--case", default=None, help="только один кейс по id")
    p.add_argument("--judge", action="store_true", help="LLM-as-judge (только с --refresh)")
    p.add_argument("--out", default=DEFAULT_OUT, help=f"каталог результатов (default: {DEFAULT_OUT})")
    args = p.parse_args()

    cases = load_cases(args.case)

    if args.refresh:
        asyncio.run(cmd_refresh(cases, args.out, args.judge))
    else:
        return cmd_assert(cases, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
