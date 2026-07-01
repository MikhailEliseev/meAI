"""Test script: Phase 0 (PERPLEXITY) → Phase 4 (KEY PERSONS) for arclinic.ru"""
import asyncio, json, logging, sys, os

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("phase-test")

# Ensure /opt/hermes is on path
sys.path.insert(0, "/opt/hermes")

from app.pipeline.states import PipelineState
from app.pipeline.phases import PHASE_0_PERPLEXITY, PHASE_4_KEY_PERSONS
from app.pipeline.engine import PipelineEngine

async def main():
    engine = PipelineEngine()
    state = PipelineState(
        session_id="test-arclinic",
        client_url="https://arclinic.ru",
        client_name="Arclinic",
        mode="ONBOARDING",
    )

    # ── City detection ──
    city = await engine._detect_city_from_contacts("https://arclinic.ru")
    if city:
        state.client_city = city
        logger.info("City: %s", city)
    else:
        state.client_city = "Москва"
        logger.warning("City: fallback to Москва")

    # ── Specialization detection ──
    spec = await engine._detect_specialization("https://arclinic.ru")
    if spec:
        state.client_specialization = spec
        logger.info("Specialization: %s", spec)
    else:
        state.client_specialization = "косметология"
        logger.warning("Specialization: fallback to косметология")

    print("\n" + "=" * 70)
    print("PHASE 0: PERPLEXITY")
    print("=" * 70)

    # ── Run Phase 0 ──
    result_0 = await engine._execute_phase(PHASE_0_PERPLEXITY, state)
    print(f"\nStatus: {result_0.status.value}")
    print(f"Duration: {result_0.duration_seconds}s")
    print(f"Data keys: {list(result_0.data.keys()) if result_0.data else 'none'}")

    if result_0.data:
        state.accumulated_data["PERPLEXITY"] = result_0.data
    if result_0.llm_interpretation:
        state.accumulated_data["PERPLEXITY_interpretation"] = result_0.llm_interpretation
        print(f"\n--- Perplexity Interpretation (first 500 chars) ---")
        print(result_0.llm_interpretation[:500])

    print("\n" + "=" * 70)
    print("PHASE 4: KEY PERSONS (with Perplexity context)")
    print("=" * 70)

    # ── Run Phase 1 ──
    result_1 = await engine._execute_phase(PHASE_4_KEY_PERSONS, state)
    print(f"\nStatus: {result_1.status.value}")
    print(f"Duration: {result_1.duration_seconds}s")
    print(f"Data keys: {list(result_1.data.keys()) if result_1.data else 'none'}")

    if result_1.llm_interpretation:
        print(f"\n--- KEY PERSONS Interpretation (first 800 chars) ---")
        print(result_1.llm_interpretation[:800])

    # ── PERPLEXITY_USED status ──
    pu_key = "KEY PERSONS_perplexity_used"
    pu_val = state.accumulated_data.get(pu_key, "NOT FOUND")
    print(f"\n>>> PERPLEXITY_USED for KEY PERSONS: {pu_val}")

    # ── All accumulated keys ──
    print(f"\n>>> All accumulated_data keys: {list(state.accumulated_data.keys())}")

    # Save to file for inspection
    output = {
        "city": state.client_city,
        "specialization": state.client_specialization,
        "phase_0_status": result_0.status.value,
        "phase_0_data_summary": {k: v[:200] if isinstance(v, str) else "non-string" for k, v in (result_0.data or {}).items()},
        "phase_0_interpretation": (result_0.llm_interpretation or "")[:1000],
        "phase_1_status": result_1.status.value,
        "phase_1_data_summary": {k: v[:200] if isinstance(v, str) else "non-string" for k, v in (result_1.data or {}).items()},
        "phase_1_interpretation": (result_1.llm_interpretation or "")[:1000],
        "perplexity_used_markers": {k: v for k, v in state.accumulated_data.items() if "perplexity_used" in k},
    }
    with open("/tmp/phase_test_result.json", "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("\nFull results saved to /tmp/phase_test_result.json")

asyncio.run(main())
