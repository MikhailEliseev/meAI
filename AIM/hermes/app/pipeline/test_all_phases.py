"""Full pipeline test: all 13 phases for arclinic.ru — error detection."""
import asyncio, json, logging, sys, os, time

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("full-test")

sys.path.insert(0, "/opt/hermes")
from app.pipeline.states import PipelineState, PhaseStatus
from app.pipeline.phases import PHASES
from app.pipeline.engine import PipelineEngine

async def main():
    engine = PipelineEngine()
    state = PipelineState(
        session_id="full-test-arclinic",
        client_url="https://arclinic.ru",
        client_name="Arclinic",
        mode="ONBOARDING",
    )

    # ── Pre-flight: city + specialization ──
    city = await engine._detect_city_from_contacts("https://arclinic.ru")
    state.client_city = city or "Москва"
    spec = await engine._detect_specialization("https://arclinic.ru")
    state.client_specialization = spec or "косметология"

    print(f"City: {state.client_city}")
    print(f"Specialization: {state.client_specialization[:80]}...")
    print(f"\n{'='*70}")

    results = []

    for phase in PHASES:
        t0 = time.time()
        phase_name = phase.name
        phase_id = phase.id

        print(f"\n── Phase {phase_id}: {phase_name} ──")
        print(f"   Tools: {phase.tools or '(LLM-only)'}")
        sys.stdout.flush()

        try:
            result = await engine._execute_phase(phase, state)
            duration = round(time.time() - t0, 1)

            # Store data
            if result.data:
                state.accumulated_data[phase_name] = result.data
            if result.llm_interpretation:
                state.accumulated_data[f"{phase_name}_interpretation"] = result.llm_interpretation

            # Extract tool-level errors
            tool_errors = {}
            tool_data_quality = {}
            for tool_name, tool_result in (result.data or {}).items():
                try:
                    parsed = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
                    if isinstance(parsed, dict) and "error" in parsed:
                        tool_errors[tool_name] = parsed["error"]
                    else:
                        tool_data_quality[tool_name] = len(tool_result) if isinstance(tool_result, str) else "non-string"
                except (json.JSONDecodeError, TypeError):
                    tool_data_quality[tool_name] = len(tool_result) if isinstance(tool_result, str) else "non-string"

            # Get PERPLEXITY_USED
            pu_marker = state.accumulated_data.get(f"{phase_name}_perplexity_used", "N/A (no interpretation)")

            entry = {
                "phase_id": phase_id,
                "phase_name": phase_name,
                "status": result.status.value,
                "duration_s": duration,
                "tools_called": list(result.data.keys()) if result.data else [],
                "tool_errors": tool_errors,
                "tool_data_quality": tool_data_quality,
                "interpretation_len": len(result.llm_interpretation) if result.llm_interpretation else 0,
                "perplexity_used": pu_marker,
                "has_data": bool(result.data and any(
                    len(v) > 200 for v in result.data.values() if isinstance(v, str)
                )),
            }

            # Determine issue level
            issues = []
            if result.status == PhaseStatus.PERMANENT_FAILURE:
                issues.append("🔴 PERMANENT_FAILURE")
            if result.status == PhaseStatus.NO_DATA:
                if phase.contract.allow_no_data:
                    # Check if it's a legitimate no-data or a tool failure
                    if tool_errors:
                        issues.append(f"🟡 NO_DATA (tools failed: {list(tool_errors.keys())})")
                    else:
                        issues.append("🟢 NO_DATA (legitimate)")
                else:
                    issues.append(f"🔴 NO_DATA (allow_no_data=False!)")
            if tool_errors:
                for tname, terr in tool_errors.items():
                    issues.append(f"🔴 {tname}: {terr[:120]}")
            if result.llm_interpretation and len(result.llm_interpretation) < 100:
                issues.append(f"🟡 Interpretation too short: {len(result.llm_interpretation)} chars")
            if phase.llm_interpret and phase.interpretation_prompt and not result.llm_interpretation:
                issues.append("🔴 Missing interpretation")
            if "MISSING" in str(pu_marker):
                issues.append("🟡 PERPLEXITY_USED: MISSING")
            elif "NO —" in str(pu_marker):
                issues.append("🟡 PERPLEXITY_USED: NO")

            entry["issues"] = issues

            status_icon = "✅" if result.status in (PhaseStatus.COMPLETED, PhaseStatus.NO_DATA) else "🔴"
            print(f"   {status_icon} {result.status.value} | {duration}s | interp={entry['interpretation_len']}chars | PU={pu_marker[:80]}")
            if issues:
                for iss in issues:
                    print(f"      {iss}")

        except Exception as e:
            entry = {
                "phase_id": phase_id,
                "phase_name": phase_name,
                "status": "CRASH",
                "duration_s": round(time.time() - t0, 1),
                "issues": [f"🔴 CRASH: {str(e)[:200]}"],
            }
            print(f"   🔴 CRASH: {e}")

        results.append(entry)

    # ── Summary ──
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    total = len(results)
    completed = sum(1 for r in results if r["status"] in ("completed", "no_data"))
    crashes = sum(1 for r in results if r["status"] == "CRASH")
    with_data = sum(1 for r in results if r.get("has_data"))
    with_errors = sum(1 for r in results if r.get("tool_errors"))

    print(f"Total phases: {total}")
    print(f"Completed/NO_DATA: {completed} | Crashes: {crashes}")
    print(f"Phases with real data: {with_data}")
    print(f"Phases with tool errors: {with_errors}")

    print(f"\nPer-phase breakdown:")
    for r in results:
        icon = "✅" if r["status"] in ("completed", "no_data") and not r.get("issues") else "⚠️"
        issues_str = "; ".join(r["issues"]) if r["issues"] else "clean"
        print(f"  {icon} Phase {r['phase_id']:2d} {r['phase_name']:20s} | {r['status']:12s} | {r['duration_s']:5.1f}s | {issues_str}")

    # Save
    output = {
        "client": "arclinic.ru",
        "city": state.client_city,
        "specialization": state.client_specialization,
        "summary": {
            "total": total, "completed": completed, "crashes": crashes,
            "with_data": with_data, "with_errors": with_errors,
        },
        "phases": results,
    }
    with open("/tmp/full_pipeline_test.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nFull report: /tmp/full_pipeline_test.json")

asyncio.run(main())
