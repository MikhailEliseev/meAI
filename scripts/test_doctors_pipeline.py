#!/usr/bin/env python3
"""End-to-end test: Doctor Leader Discovery on real competitors.

Runs extract_doctors → SocialScanner → ArticleScanner → scoring → matrix → dialogue.

Usage: PYTHONPATH=AIM/src python3 scripts/test_doctors_pipeline.py
"""

import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "AIM/src")

import httpx
from bs4 import BeautifulSoup

from aim.services.ci.models import DoctorInfo, DoctorSocialResult, CompetitorFull
from aim.services.ci.doctor_extractor import (
    extract_doctors,
    compute_influence_score,
    identify_leaders,
)
from aim.services.ci import SocialScanner, ArticleScanner, SeoAuditor
from aim.services.ci.apify_social_finder import ApifySocialFinder
from aim.services.ci.comparison_matrix import ComparisonMatrixBuilder
from aim.services.ci.dialogue_manager import DialogueManager


# ---------------------------------------------------------------------------
# Simplified pipeline
# ---------------------------------------------------------------------------


async def analyze_competitor(name: str, url: str) -> CompetitorFull:
    """Run collectors for a single competitor."""
    full = CompetitorFull(name=name, url=url)

    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # ---- 1. Website + Doctors ----
        print(f"  🌐 Захожу на сайт {name}...")
        soup = None
        try:
            resp = await client.get(url, headers=headers)
            soup = BeautifulSoup(resp.text, "html.parser")
            doctor_names = extract_doctors(soup, url)
            print(f"     Найдено врачей: {len(doctor_names)}")
            for d in doctor_names:
                extra = f" ({d.get('specialty', '')[:40]})" if d.get('specialty') else ""
                print(f"     - {d['name']}{extra}")
        except Exception as e:
            print(f"     ⚠️ Ошибка сайта: {e}")
            doctor_names = []

        # ---- 2. SEO Audit ----
        print(f"  🔍 SEO аудит {name}...")
        try:
            auditor = SeoAuditor()
            seo_result = auditor.audit(url)
            full.seo = seo_result
            print(f"     Score: {seo_result.score}/100, Issues: {len(seo_result.issues)}")
        except Exception as e:
            print(f"     ⚠️ SEO: {e}")

    # ---- 3. Doctors enrichment (social + articles) ----
    if doctor_names:
        print(f"  👨‍⚕️ Анализирую врачей {name} (первые {min(5, len(doctor_names))})...")
        full.doctors = await _enrich_doctors(doctor_names)
        if full.doctors:
            for d in full.doctors[:3]:
                leader_mark = "⭐" if d.is_leader else "  "
                arts = d.articles.total_found if d.articles else 0
                print(f"     {leader_mark} {d.name} — influence={d.influence_score:.1f}/100, articles={arts}")
    else:
        print(f"  ⚠️ Врачи не найдены на сайте {name}")

    return full


async def _enrich_doctors(doctor_names: list[dict]) -> list[DoctorInfo]:
    """For each doctor (up to 5): batch Apify social + articles scan."""
    names_to_scan = doctor_names[:5]
    all_names = [doc.get("name", "") for doc in names_to_scan]
    loop = asyncio.get_event_loop()

    social_scanner = SocialScanner()
    article_scanner = ArticleScanner()

    # Batch Apify social search
    apify_results: dict[str, DoctorSocialResult] = {}
    if all_names:
        try:
            print(f"  🔍 Apify: ищем соцсети {len(all_names)} врачей…")
            apify_finder = ApifySocialFinder()
            apify_results = await apify_finder.find_doctors(all_names)
            for name, sr in apify_results.items():
                if sr.platforms_found > 0:
                    print(f"     Apify нашёл {sr.platforms_found} платформ для {name}: "
                          f"{[(p.platform, p.handle) for p in sr.profiles if p.exists]}")
        except Exception as e:
            print(f"     ⚠️ Apify batch failed: {e}")

    async def _scan_one(doc: dict) -> DoctorInfo:
        name = doc.get("name", "")
        d = DoctorInfo(
            name=name,
            specialty=doc.get("specialty", ""),
            photo_url=doc.get("photo_url", ""),
            bio_url=doc.get("bio_url", ""),
        )

        with ThreadPoolExecutor(max_workers=3) as pool:
            social_future = loop.run_in_executor(pool, social_scanner.scan_doctor, name)
            articles_future = loop.run_in_executor(pool, article_scanner.search_author, name, doc.get("specialty", ""))
            pd_future = loop.run_in_executor(pool, social_scanner.search_prodoctorov_doctor, name)

            try:
                d.social = await social_future
            except Exception as e:
                print(f"       ⚠️ Соцсети {name}: {e}")

            # Merge Apify results — replace SocialScanner placeholders
            apify_social = apify_results.get(d.name)
            if apify_social and apify_social.profiles:
                if d.social is None:
                    d.social = apify_social
                else:
                    for ap in apify_social.profiles:
                        if not ap.exists:
                            continue
                        replaced = False
                        for i, existing in enumerate(d.social.profiles):
                            if existing.platform == ap.platform and not existing.exists:
                                d.social.profiles[i] = ap
                                replaced = True
                                break
                        if not replaced:
                            d.social.profiles.append(ap)
                    d.social.platforms_found = sum(1 for p in d.social.profiles if p.exists)

            try:
                d.articles = await articles_future
            except Exception as e:
                print(f"       ⚠️ Статьи {name}: {e}")

            try:
                pd_rating, pd_reviews = await pd_future
                d.prodoctorov_rating = pd_rating
                d.prodoctorov_reviews = pd_reviews
                if pd_rating > 0:
                    print(f"       📋 ProDoctorov: {pd_rating}/5 ({pd_reviews} отзывов)")
            except Exception as e:
                print(f"       ⚠️ ProDoctorov {name}: {e}")

        d.influence_score = compute_influence_score(d)
        return d

    results = []
    for doc in names_to_scan:
        r = await _scan_one(doc)
        results.append(r)

    doctors = [r for r in results if isinstance(r, DoctorInfo)]
    return identify_leaders(doctors)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("=" * 70)
    print("🚀 DOCTOR LEADER DISCOVERY — ПОЛНЫЙ ТЕСТ")
    print("=" * 70)
    print()

    competitors = [
        ("ЛИНЛАЙН", "https://www.linline.ru"),
        ("Медси", "https://medsi.ru/doctors/"),
    ]

    results: list[CompetitorFull] = []
    for name, url in competitors:
        print(f"🏥 {name} ({url})")
        cf = await analyze_competitor(name, url)
        results.append(cf)
        print()

    # ---- Build comparison matrix ----
    print("=" * 70)
    print("📋 МАТРИЦА СРАВНЕНИЯ")
    print("=" * 70)

    builder = ComparisonMatrixBuilder()
    matrix = builder.build(
        client_url="https://arclinic.ru",
        client_features={"сайт": True, "соцсети": True, "прайс": False},
        competitors_full=results,
        client_name="ARclinic",
    )

    ctx = builder.to_llm_context(matrix)
    data = json.loads(ctx)

    for c in data.get("competitors", []):
        print(f"\n🏥 {c['name']}:")
        doctors = c.get("doctors", [])
        if doctors:
            for d in doctors:
                leader = "⭐" if d.get("is_leader") else "  "
                s = d.get("social", {})
                print(f"  {leader} {d['name']}")
                print(f"     Influence: {d['influence_score']}/100")
                print(f"     Followers: {s.get('total_followers', 0):,}")
                print(f"     Platforms: {s.get('platforms_found', 0)}")
                print(f"     Articles: {d.get('articles_count', 0)}")
                print(f"     Topics: {', '.join(s.get('top_topics', []))}")
                print(f"     Journals: {', '.join(d.get('top_journals', []))}")
        else:
            print(f"  ⚠️ Нет данных о врачах")

    # ---- Dialogue ----
    print("\n" + "=" * 70)
    print("💬 ДИАЛОГ (пресейл)")
    print("=" * 70)

    mgr = DialogueManager()
    hook = mgr.build_hook_prompt(matrix)
    print(f"\n📌 HOOK PROMPT:\n{hook[:1200]}...\n")

    print("📋 FALLBACK (секция врачей-лидеров):")
    fallback = mgr._fallback_response(matrix)
    lines = fallback.split("\n")
    in_doctors = False
    for line in lines:
        if "Врачи-лидеры" in line or "Врач" in line:
            in_doctors = True
        if in_doctors:
            print(line)
            if line.strip() == "" and in_doctors:
                break

    print("\n✅ ГОТОВО!")


asyncio.run(main())
