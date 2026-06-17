"""Re-run failed tools for nachalo-clinica session with working Firecrawl keys.

Usage: docker exec aim-hermes python /opt/hermes/re-run_tools.py
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Ensure /opt/hermes is on sys.path for imports
sys.path.insert(0, "/opt/hermes")
sys.path.insert(0, "/opt/hermes/app")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("re-run")

SESSIONS_ROOT = Path("/opt/data/sessions-archive")
SESSION_HASH = "nachalo-clinicaru"
COMPANY_NAME = "Семейная клиника Начало"
CITY = "Ростов-на-Дону"
WEBSITE = "https://nachalo-clinica.ru"


def save_result(filename: str, data):
    """Save tool result to session archive."""
    session_dir = SESSIONS_ROOT / SESSION_HASH
    session_dir.mkdir(parents=True, exist_ok=True)
    filepath = session_dir / filename
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info("Saved %s (%d bytes)", filename, filepath.stat().st_size)


async def run_tool(name: str, handler, **kwargs):
    """Run a tool and save its JSON output."""
    logger.info("=== Running %s ===", name)
    try:
        result_json = await handler(**kwargs)
        # Parse JSON string result
        if isinstance(result_json, str):
            data = json.loads(result_json)
        else:
            data = result_json
        return data
    except Exception as e:
        logger.error("%s failed: %s", name, e)
        return {"error": str(e)}


async def main():
    logger.info("Re-running 4 failed tools for %s (%s)", COMPANY_NAME, SESSION_HASH)

    # CRITICAL: Initialize Firecrawl key bank BEFORE importing tools
    from tools.firecrawl_key_bank import init as fk_init, active_count
    fk_init()
    logger.info("Firecrawl key bank initialized: %d active keys", active_count())

    # 1. Review Platforms
    from tools.run_review_platforms import handle_run_review_platforms
    reviews = await run_tool(
        "review_platforms",
        handle_run_review_platforms,
        company_name=COMPANY_NAME,
        city=CITY,
    )
    if reviews and "error" not in reviews:
        save_result("review_platforms.json", reviews)
    else:
        logger.warning("review_platforms returned no data, keeping existing file")

    # 2. SMI Mentions
    from tools.run_smi_mentions import handle_run_smi_mentions
    smi = await run_tool(
        "smi_mentions",
        handle_run_smi_mentions,
        company_name=COMPANY_NAME,
    )
    if smi and "error" not in smi:
        save_result("smi_mentions.json", smi)
    else:
        logger.warning("smi_mentions returned no data, keeping existing file")

    # 3. Ads Intelligence
    from tools.run_ads_intelligence import handle_run_ads_intelligence
    ads = await run_tool(
        "ads_intelligence",
        handle_run_ads_intelligence,
        company_name=COMPANY_NAME,
        website=WEBSITE,
    )
    if ads and "error" not in ads:
        save_result("ads_intelligence.json", ads)
    else:
        logger.warning("ads_intelligence returned no data, keeping existing file")

    # 4. Doctor Dossiers
    from tools.run_doctor_dossiers import handle_run_doctor_dossiers
    doctors = await run_tool(
        "doctor_dossiers",
        handle_run_doctor_dossiers,
        doctor_name=COMPANY_NAME,
    )
    if doctors and "error" not in doctors:
        save_result("doctor_dossiers.json", doctors)
    else:
        logger.warning("doctor_dossiers returned no data, keeping existing file")

    logger.info("=== All tools re-run complete ===")
    logger.info("Session dir: %s", SESSIONS_ROOT / SESSION_HASH)


if __name__ == "__main__":
    asyncio.run(main())
