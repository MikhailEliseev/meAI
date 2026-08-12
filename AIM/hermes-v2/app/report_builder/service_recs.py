"""Рекомендации услуг AIM на основании найденных слабых мест клиники.

Каждое слабое место аудита → конкретная услуга из iamaim.ru/prices/
с ценой и обоснованием («почему именно это вам нужно»).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Каталог услуг AIM (iamaim.ru/prices/)
SERVICES = {
    "seo_geo": {
        "name": "SEO + GEO продвижение",
        "price": "56 000 ₽/мес",
        "desc": "Рост видимости сайта в поиске и на картах",
    },
    "smm": {
        "name": "SMM (VK + Instagram)",
        "price": "59 000 ₽/мес",
        "desc": "Ведение соцсетей: контент, постинг, автоворонки",
    },
    "maps": {
        "name": "Карты + агрегаторы + поведенческий",
        "price": "34 000 ₽/мес",
        "desc": "Карточки на Яндекс/Google Картах, ПроДокторов, отзывы",
    },
    "performance": {
        "name": "Performance-маркетинг",
        "price": "19 000 ₽/мес + бюджет",
        "desc": "Контекстная реклама (Яндекс.Директ), креативы, A/B",
    },
    "tech": {
        "name": "Техподдержка сайта",
        "price": "19 000 ₽/мес",
        "desc": "Обновления, бэкапы, скорость, мониторинг",
    },
    "messengers": {
        "name": "Мессенджеры и каналы",
        "price": "49 000 ₽/мес",
        "desc": "WhatsApp/Telegram-каналы, контент, автоворонки",
    },
    "ai_bot": {
        "name": "AI-продавцы / AI-боты",
        "price": "34 000 ₽/мес",
        "desc": "Бот на сайт и в чаты: запись к врачам, фильтрация лидов",
    },
    "monitoring": {
        "name": "Мониторинг маркетинговых показателей",
        "price": "24 000 ₽/мес",
        "desc": "Контроль конкурентов, позиций, цен, отзывов, дашборды",
    },
    "site_rebuild": {
        "name": "Переработка сайта на CMS",
        "price": "от 250 000 ₽",
        "desc": "Полный редизайн на 1С-Битрикс или WordPress",
    },
    "creatives": {
        "name": "Генерация креативов (фото/видео)",
        "price": "79 000 ₽/мес",
        "desc": "Нейровидео, цифровые аватары врачей, ИИ-фотосессии",
    },
    "call_audit": {
        "name": "Анализ колл-центра",
        "price": "49 000 ₽ (разово)",
        "desc": "Прослушка звонков, скрипты, конверсия в запись",
    },
}


def recommend_services(
    audit: dict | None,
    profile: dict | None,
    reviews: dict | None,
    competitors: dict | None,
) -> list[dict]:
    """Сопоставить найденные слабые места с услугами AIM.

    Возвращает список рекомендаций:
      [{"service_id", "name", "price", "desc", "rationale"}]
    rationale — привязка к конкретному слабому месту (почему это вам).
    """
    # Защита: гарантируем dict на входе (могут прийти строки из JSON)
    if not isinstance(audit, dict):
        audit = {}
    if not isinstance(profile, dict):
        profile = {}
    if not isinstance(reviews, dict):
        reviews = {}
    if not isinstance(competitors, dict):
        competitors = {}
    recs: list[dict] = []

    def _add(sid: str, rationale: str) -> None:
        svc = SERVICES.get(sid)
        if svc and sid not in {r["service_id"] for r in recs}:
            recs.append({"service_id": sid, **svc, "rationale": rationale})

    # ── 1. SEO/GEO слабость ──
    geo = audit.get("geo_score", 0) or 0
    has_med_schema = bool(audit.get("schema", {}).get("medical"))
    has_meta = bool(audit.get("meta_description"))
    has_og = bool(audit.get("og_tags"))
    seo_issues = []
    if geo and geo < 75:
        seo_issues.append(f"GEO Score {geo}/100")
    if not has_med_schema:
        seo_issues.append("нет MedicalBusiness Schema")
    if not has_meta:
        seo_issues.append("нет meta description")
    if not has_og:
        seo_issues.append("нет Open Graph")
    if seo_issues:
        _add("seo_geo", f"{', '.join(seo_issues)} — вас плохо находят в поиске")

    # ── 2. Соцсети слабые / нет VK ──
    socials = profile.get("socials_found") or {}
    if isinstance(socials, dict):
        has_vk = bool(socials.get("vk"))
    else:
        has_vk = "vk" in str(socials).lower()
    vk_followers = audit.get("vk_followers", 0) or 0
    if not has_vk:
        _add("smm", "Нет VK — конкуренты активно используют соцсети, вы теряете охват")
    elif vk_followers and vk_followers < 2000:
        _add("smm", f"VK всего {vk_followers} подписчиков — мало для клиники вашего масштаба")

    # ── 3. Отзывы / карты — разрыв между площадками ──
    # platforms = {"yandex": {"rating":4.0,"reviews":12}, "twogis":{}, ...}
    platforms = reviews.get("platforms", {})
    if isinstance(platforms, dict):
        yandex = platforms.get("yandex", {}) or {}
        gis2 = platforms.get("twogis") or platforms.get("2gis") or platforms.get("gis2") or {}
        yr = (yandex.get("rating") if isinstance(yandex, dict) else 0) or 0
        yc = (yandex.get("reviews") if isinstance(yandex, dict) else 0) or 0
        gr = (gis2.get("rating") if isinstance(gis2, dict) else 0) or 0
        gc = (gis2.get("reviews") if isinstance(gis2, dict) else 0) or 0
        if yr and gr and (yr - gr) >= 0.4:
            _add("maps", f"Разрыв рейтинга: Яндекс {yr}★ vs 2ГИС {gr}★ — нужно подтянуть 2ГИС")
        elif yc and gc and gc < yc * 0.1:
            _add("maps", f"На 2ГИС всего {gc} отзывов при {yc} на Яндекс — слабая карточка")
        elif yc and yc < 50:
            _add("maps", f"Всего {yc} отзывов на Яндекс — мало для доверия пациентов")

    # ── 4. Нет Telegram/WhatsApp канала ──
    if isinstance(socials, dict):
        has_tg = bool(socials.get("telegram"))
    else:
        has_tg = "telegram" in str(socials).lower()
    if not has_tg:
        _add("messengers", "Нет Telegram-канала — упускаете удержание пациентов через мессенджеры")

    # ── 5. Технические проблемы сайта ──
    perf = audit.get("perf_estimate", "")
    ssr = audit.get("ssr")
    cms = profile.get("website_platform", "") or ""
    if perf == "низкая":
        _add("tech", "Сайт медленный (низкая скорость загрузки) — пациенты уходят")
    elif not ssr:
        _add("tech", "Нет SSR — поисковики плохо индексируют страницы")

    # ── 6. AI-бот (всегда актуально для клиник) ──
    _add("ai_bot", "Запись через AI-бота 24/7 — не теряйте пациентов ночью и в выходные")

    # ── 7. Мониторинг (мы только что сделали аудит — предложим регулярный) ──
    _add("monitoring", "Регулярный контроль конкурентов, позиций, отзывов — как этот отчёт, но ежемесячно")

    return recs


def format_service_recommendations(recs: list[dict]) -> str:
    """Форматировать рекомендации как блок для отчёта (Markdown).
    ВАЖНО: используем обычный markdown (##, **, списки) — НЕ :::директивы,
    т.к. этот текст рендерится через _interpretation_to_html, который
    :::директивы не понимает (они вылезают как сырой текст)."""
    if not recs:
        return ""
    lines = ["## Как мы поможем", ""]
    lines.append("**На основе найденных слабых мест — какие услуги AIM их закроют:**")
    lines.append("")
    for r in recs:
        lines.append(f"- **{r['name']}** — {r['price']}")
        lines.append(f"  {r['rationale']}.")
        lines.append(f"  *{r['desc']}*")
        lines.append("")
    lines.append("**Полный список услуг:** [iamaim.ru/prices](https://iamaim.ru/prices/)")
    return "\n".join(lines)
