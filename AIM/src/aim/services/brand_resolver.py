"""Brand → INN resolver via bo.nalog.gov.ru.

Takes a brand name (e.g. "Seline", "Клазко", "GMTClinic") and resolves it
to a real legal entity (ИНН) using ФНС registry search, filtered by medical
OKVED codes and ranked by revenue.

This replaces the broken rusprofile-based _enrich_gm_via_inn (0/48 hit rate)
with a reliable bo.nalog.gov.ru lookup (validated on Фрау Клиник, Клазко, GMT).
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from src.aim.services.nalog import BfoNalogClient

logger = logging.getLogger(__name__)

# Medical OKVED prefixes — only return companies in healthcare
MEDICAL_OKVED_PREFIXES = ("86.",)

# Minimum INN length for a valid legal entity
_MIN_INN_LEN = 10


@dataclass
class ResolvedBrand:
    """A brand resolved to a real legal entity in ФНС."""

    brand_query: str  # original brand name queried
    inn: str
    org_id: int  # bo.nalog numeric ID for financials lookup
    legal_name: str
    okved: str
    latest_revenue: Optional[int]  # RUB (gainSum × 1000)
    status: str = ""
    address: str = ""

    @property
    def is_medical(self) -> bool:
        return any(self.okved.startswith(p) for p in MEDICAL_OKVED_PREFIXES)


def _resolve_sync(
    nalog: BfoNalogClient,
    brand_name: str,
    okved_prefix: str,
) -> Optional[ResolvedBrand]:
    """Synchronous resolution — called via asyncio.to_thread."""
    results = nalog.search(brand_name)
    if not results:
        return None

    # Filter by OKVED prefix (medical) if any match
    medical = [r for r in results if r.okved2 and r.okved2.startswith(okved_prefix)]
    pool = medical if medical else results

    # Rank by latest_revenue descending — the biggest entity is most likely
    # the operating legal entity behind a known brand
    pool.sort(key=lambda r: r.latest_revenue or 0, reverse=True)

    best = pool[0]
    if not best.inn or len(best.inn) < _MIN_INN_LEN:
        return None

    # gainSum from bo.nalog is in thousands of rubles
    revenue_rub = best.latest_revenue * 1000 if best.latest_revenue else None

    return ResolvedBrand(
        brand_query=brand_name,
        inn=best.inn,
        org_id=best.id,
        legal_name=best.short_name,
        okved=best.okved2,
        latest_revenue=revenue_rub,
        status=best.status,
        address=best.address,
    )


async def resolve_brand_to_inn(
    brand_name: str,
    okved_prefix: str = "86.",
    nalog: Optional[BfoNalogClient] = None,
) -> Optional[ResolvedBrand]:
    """Resolve a brand name to a legal entity (ИНН) via bo.nalog.gov.ru.

    Pipeline:
      1. Search ФНС by brand name
      2. Filter by OKVED prefix (medical = 86.xx)
      3. Pick the entity with highest revenue (most likely the real operator)
      4. Return ResolvedBrand or None if not found

    Anti-hallucination: if a brand doesn't exist in ФНС, returns None.
    This naturally filters out fabricated competitors from LLM outputs.

    Args:
        brand_name: Brand name to resolve (e.g. "Клазко", "GMTClinic").
        okved_prefix: OKVED prefix to filter (default: "86." for medical).
        nalog: Optional BfoNalogClient instance (creates one if not provided).

    Returns:
        ResolvedBrand with INN and org_id, or None if not found in ФНС.
    """
    own_client = nalog is None
    client = nalog or BfoNalogClient()
    try:
        result = await asyncio.to_thread(_resolve_sync, client, brand_name, okved_prefix)
        if result:
            logger.info(
                "brand_resolved: brand=%s → inn=%s okved=%s revenue=%s",
                brand_name, result.inn, result.okved,
                f"{result.latest_revenue:,}" if result.latest_revenue else "N/A",
            )
        else:
            logger.info("brand_not_found_in_fns: brand=%s", brand_name)
        return result
    finally:
        if own_client:
            client.close()


async def resolve_brands_batch(
    brand_names: list[str],
    okved_prefix: str = "86.",
    max_concurrent: int = 5,
) -> list[Optional[ResolvedBrand]]:
    """Resolve multiple brands to INNs concurrently.

    Uses a single shared BfoNalogClient (its internal rate limiter handles
    concurrency at 5 req/s). Results are in the same order as input.

    Args:
        brand_names: List of brand names to resolve.
        okved_prefix: OKVED prefix filter.
        max_concurrent: Max parallel resolutions.

    Returns:
        List of ResolvedBrand or None, same order as input.
    """
    nalog = BfoNalogClient()
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _semaphored(brand: str) -> Optional[ResolvedBrand]:
        async with semaphore:
            return await resolve_brand_to_inn(brand, okved_prefix, nalog)

    try:
        results = await asyncio.gather(
            *[_semaphored(b) for b in brand_names],
            return_exceptions=True,
        )
    finally:
        nalog.close()

    # Convert exceptions to None
    return [r if isinstance(r, ResolvedBrand) else None for r in results]
