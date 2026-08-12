"""Детерминированные проверки качества ответа (G1-G5).

Работают на snapshot — быстрые, бесплатные, без вызова LLM.
Каждая проверка возвращает dict с score/pass/деталями.

Главная — G1 Grounding: измеряет ровно дефект P0-1
(«LLM не видит данные»). Если LLM cite-ит цифры, которых нет в
formatted_blocks — он галлюцинирует (т.к. данные от него скрыты).
"""
from __future__ import annotations

import re


# ────────────────────────────────────────────────────────────────────
# Утилиты нормализации чисел
# ────────────────────────────────────────────────────────────────────

def normalize_num(s: str) -> str:
    """Приводит число к каноничному виду для сравнения.
    '4,8' → '4.8', '380' → '380', '1 200' → '1200'."""
    s = s.strip().replace(" ", "").replace("\xa0", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    s = s.strip(".")
    return s


def _is_year(n: str) -> bool:
    return n.isdigit() and 2010 <= int(n) <= 2035


# ────────────────────────────────────────────────────────────────────
# G1. GROUNDING — опирается ли LLM на данные
# ────────────────────────────────────────────────────────────────────

# Числа рядом со смысловыми единицами = фактические утверждения
_CLAIM_UNITS = re.compile(
    r"(\d[\d\s.,]*?\d|\d)\s*"
    r"(млн|млрд|тыс|тысяч|₽|руб|star|★|звёзд|звезд|отзыв|отзывов|"
    r"врач|врачей|специалист|клиник|филиал|раз|лет|года|лет|"
    r"человек|сотрудник|сотрудников|мест|площадок)",
    re.I,
)
# Рейтинг явно: «4.8★» / «4,8 star»
_RATING = re.compile(r"(\d[.,]\d)\s*(?:★|star|звёзд)", re.I)
# Выручка/прибыль: «380 млн» / «1.2 млрд»
_REVENUE = re.compile(r"(\d[\d\s.,]*)\s*(млн|млрд)\s*₽?", re.I)
# ИНН — 10 цифр
_INN = re.compile(r"\b(\d{10})\b")
# ОГРН — 13 или 15 цифр
_OGRN = re.compile(r"\b(\d{13,15})\b")


def extract_claims(text: str) -> dict:
    """Извлекает из текста LLM «утверждения» (числа/сущности),
    которые ДОЛЖНЫ быть grounded в данных."""
    claims: dict[str, list[str]] = {"numbers": [], "ratings": [], "revenues": [], "inn": [], "ogrn": []}

    for m in _CLAIM_UNITS.finditer(text):
        n = normalize_num(m.group(1))
        if n and not _is_year(n):
            claims["numbers"].append(n)
    for m in _RATING.finditer(text):
        claims["ratings"].append(normalize_num(m.group(1)))
    for m in _REVENUE.finditer(text):
        claims["revenues"].append(normalize_num(m.group(1)))
    for m in _INN.finditer(text):
        claims["inn"].append(m.group(1))
    for m in _OGRN.finditer(text):
        # ОГРН 13/15 цифр — не путать с ИНН/телефонами
        if len(m.group(1)) in (13, 15):
            claims["ogrn"].append(m.group(1))

    # Дедуп, сохраняя порядок
    for k in claims:
        seen, out = set(), []
        for c in claims[k]:
            if c not in seen:
                seen.add(c)
                out.append(c)
        claims[k] = out
    return claims


def _in_corpus(num: str, corpus: str) -> bool:
    """Есть ли число в корпусе данных (с учётом вариантов записи).
    Десятичные (4.2) должны совпадать точно — иначе рейтинг 4.2
    ложно matched бы с 4.8 через целую часть."""
    if not num:
        return False
    if num in corpus:
        return True
    # «4.8» может быть в корпусе как «4,8»
    alt = num.replace(".", ",")
    if alt in corpus:
        return True
    return False


def check_grounding(llm_text: str, formatted_blocks: list[str]) -> dict:
    """G1: каждая цифра/сущность в тексте LLM должна быть в данных.
    Возвращает score% + примеры ungrounded (потенциальных галлюцинаций)."""
    corpus = "\n".join(formatted_blocks)
    claims = extract_claims(llm_text)

    grounded: list[str] = []
    ungrounded: list[str] = []
    all_nums = claims["numbers"] + claims["ratings"] + claims["revenues"]
    for n in all_nums:
        (grounded if _in_corpus(n, corpus) else ungrounded).append(n)

    # ИНН/ОГРН — отдельная строгая проверка
    inn_ungrounded = [i for i in claims["inn"] if i not in corpus]
    ogrn_ungrounded = [o for o in claims["ogrn"] if o not in corpus]

    # G8: классификация ungrounded — derived (производные) vs fabricated (выдумки)
    grounded_floats = _extract_corpus_numbers(corpus)
    derived: list[str] = []
    fabricated: list[str] = []
    for n in sorted(set(ungrounded)):
        if _is_derived(n, grounded_floats):
            derived.append(n)
        else:
            fabricated.append(n)

    total = len(all_nums)
    # Скор G1: grounded + derived считаем обоснованными
    trustworthy = len(grounded) + len(derived)
    score = round(trustworthy / total * 100, 1) if total else 0.0

    return {
        "score_pct": score,
        "total_claims": total,
        "grounded_count": len(grounded),
        "ungrounded": sorted(set(ungrounded))[:20],
        "derived": derived[:15],
        "fabricated": fabricated[:15],
        "inn_ungrounded": inn_ungrounded[:5],
        "ogrn_ungrounded": ogrn_ungrounded[:5],
        "pass": score >= 60 and not inn_ungrounded and not ogrn_ungrounded,
    }


def _extract_corpus_numbers(corpus: str) -> list[float]:
    """Извлечь все числа из корпуса данных (для derivability-проверки)."""
    nums = []
    for m in re.finditer(r"\d[\d\s.,]*\d|\d", corpus):
        n = normalize_num(m.group(0))
        try:
            nums.append(float(n))
        except ValueError:
            pass
    return nums


def _is_derived(num_str: str, corpus_nums: list[float], tol: float = 0.08) -> bool:
    """Является ли число производным от данных (отношение/процент/разница)?

    Производные — легитимные: «в 2.6 раза» (a/b), «маржа 2.8%» (a/b×100),
    «на 11 млн больше» (a−b). Проверяем похожесть num на a/b, a±b, a/b×100
    для пар corpus_nums в пределах tol (8%).
    """
    if not corpus_nums:
        return False
    try:
        x = float(num_str)
    except ValueError:
        return False
    if x <= 0:
        return False
    # короткий список без dup-ов и без нулей
    basis = [n for n in corpus_nums if n > 0]
    for i, a in enumerate(basis):
        for b in basis[i + 1:]:
            for cand in (a / b, b / a, abs(a - b) / 1e6, a / b * 100, b / a * 100):
                if cand > 0 and abs(cand - x) / max(cand, x) < tol:
                    return True
        # производные от одного числа (доля, процент)
        for cand in (a / 1e6, a / 1e9, a / sum(basis) * 100 if sum(basis) else 0):
            if cand > 0 and abs(cand - x) / max(cand, x) < tol:
                return True
    return False


# ────────────────────────────────────────────────────────────────────
# G2. STRUCTURE — структура ответа по спецификации промпта
# ────────────────────────────────────────────────────────────────────

_REQUIRED_SECTIONS = [
    ("position", [r"позици", r"на\s+рынке", r"лидер", r"середняк", r"аутсайдер"]),
    ("strengths", [r"сильн", r"преимуществ", r"лучше"]),
    ("growth", [r"рост", r"пробел", r"отстаё", r"отстаю", r"отстает", r"слаб"]),
    ("reviews", [r"отзыв", r"пациент", r"говорят", r"хвалят", r"критик"]),
    ("recommendations", [r"рекоменд", r"совет", r"предлага.*действ", r"начните", r"что делать"]),
]


def check_structure(llm_text: str) -> dict:
    """G2: присутствуют ли обязательные секции ответа."""
    text_lower = llm_text.lower()
    present, missing = [], []
    for name, patterns in _REQUIRED_SECTIONS:
        if any(re.search(p, text_lower) for p in patterns):
            present.append(name)
        else:
            missing.append(name)
    return {
        "present": present,
        "missing": missing,
        "score": f"{len(present)}/{len(_REQUIRED_SECTIONS)}",
        "pass": len(missing) <= 1,
    }


# ────────────────────────────────────────────────────────────────────
# G3. CLEAN OUTPUT — нет мусора/утечек/compliance
# ────────────────────────────────────────────────────────────────────

# Сырой JSON: {...} или [...], особенно с ключами в кавычках
_RAW_JSON = re.compile(r'[{]\s*"[a-z_]+":', re.I)
# Float-артефакт: 4.300000190734863
_FLOAT_ARTIFACT = re.compile(r"\d+\.\d{5,}")
# ::: директивы markdown
_DIRECTIVES = re.compile(r"::+\s*[a-z\-]+", re.I)
# Утёкший маркер кнопок
_LEAKED_MARKER = re.compile(r"\[/?SUGGESTIONS\]", re.I)
# Запрещённые данные (нет в источниках): веб-аналитика. «трафик», «визиты сайта»,
# «трафик» — разрешён в SEO-контексте (органический/поисковый трафик — это
# легитимная тема для секции «Сайт»), запрещён только как веб-аналитика
# («трафик сайта 500 человек» — данных которых нет). Проверяем контекст в check_clean.
_BANNED_TERMS_RAW = re.compile(r"\bтрафик\b", re.I)
_BANNED_TERMS_OTHER = re.compile(
    r"\b(визит\w*\s+(?:на\s+)?сайт|посетител\w*\s+сайта|просмотр\w*\s+страниц)\b",
    re.I,
)
_TRAFFIC_OK = re.compile(
    r"(?:органический|поисковый|seo|из\s+поиск|пациент|клиент)[\s-]*трафик|"
    r"трафик\s+(?:пациент|клиент|из\s+поиск)",
    re.I,
)
# Запрещённые рекомендации (148-ФЗ) — в контексте «рекомендуйте/создайте»
_BANNED_RECS = re.compile(
    r"(рекоменд\w*|созда\w*|заводи\w*|начни\w*|открой\w*|настрой\w*)[^.]{0,60}?"
    r"(instagram|инстаграм|telegram|телеграм)",
    re.I,
)


def check_clean(llm_text: str) -> dict:
    """G3: нет сырого JSON, float-артефактов, директив, утечек, нарушений 148-ФЗ."""
    violations: list[str] = []

    if _RAW_JSON.search(llm_text):
        m = _RAW_JSON.search(llm_text)
        violations.append(f"raw JSON: …{llm_text[max(0,m.start()-20):m.end()+40]}…")
    if _FLOAT_ARTIFACT.search(llm_text):
        violations.append(f"float artifact: {_FLOAT_ARTIFACT.search(llm_text).group()}")
    if _DIRECTIVES.search(llm_text):
        violations.append(f"markdown directive ::: ({_DIRECTIVE_FIND(llm_text)})")
    if _LEAKED_MARKER.search(llm_text):
        violations.append("leaked [SUGGESTIONS] marker")
    # «трафик» — проверяем контекст: разрешён в SEO (органический/поисковый)
    if _BANNED_TERMS_RAW.search(llm_text):
        # вырезаем легитимные SEO-упоминания и проверяем остался ли «голый» трафик
        traffic_cleaned = _TRAFFIC_OK.sub("", llm_text)
        if _BANNED_TERMS_RAW.search(traffic_cleaned):
            violations.append(f"banned term (трафик без SEO-контекста)")
    if _BANNED_TERMS_OTHER.search(llm_text):
        violations.append(f"banned term: {_BANNED_TERMS_OTHER.search(llm_text).group()}")
    if _BANNED_RECS.search(llm_text):
        violations.append(f"148-ФЗ violation: {_BANNED_RECS.search(llm_text).group()}")

    return {"violations": violations, "pass": len(violations) == 0}


def _DIRECTIVE_FIND(text: str) -> str:
    m = _DIRECTIVES.search(text)
    return m.group() if m else ""


# ────────────────────────────────────────────────────────────────────
# G4. DATA COMPLETENESS — тулы вернули данные
# ────────────────────────────────────────────────────────────────────

_EXPECTED_TOOLS = ["extract_clinic_profile", "find_competitors", "run_review_platforms"]


def check_data_completeness(tool_calls: list[dict]) -> dict:
    """G4: каждый ожидаемый тул вызван и вернул непустой результат."""
    by_tool: dict[str, dict] = {}
    for tc in tool_calls:
        name = tc.get("tool", "")
        entry = by_tool.setdefault(name, {"called": False, "ok": False, "error": None})
        entry["called"] = True
        if tc.get("status") == "done":
            result = str(tc.get("result", ""))
            if result and "error" not in result.lower()[:50] and len(result) > 20:
                entry["ok"] = True
            elif "error" in result.lower():
                entry["error"] = result[:120]

    missing = [t for t in _EXPECTED_TOOLS if not by_tool.get(t, {}).get("called")]
    failed = [t for t in _EXPECTED_TOOLS if by_tool.get(t, {}).get("called") and not by_tool.get(t, {}).get("ok")]
    ok = [t for t in _EXPECTED_TOOLS if by_tool.get(t, {}).get("ok")]

    return {
        "ok": ok,
        "missing": missing,
        "failed": failed,
        "score": f"{len(ok)}/{len(_EXPECTED_TOOLS)}",
        "pass": len(ok) >= 2,  # минимум 2 из 3 должны сработать
    }


# ────────────────────────────────────────────────────────────────────
# G7. CONSISTENCY — одинаковые метрики из разных источников не расходятся
# ────────────────────────────────────────────────────────────────────
# Ловит баг типа: «04 ОТЗЫВЫ: Яндекс 5.0★ (565)» vs «03 АУДИТ: Яндекс 4.9★ (64)».
# Одна площадка должна показываться с одним рейтингом/числом отзывов.

_CONSISTENCY_PLATFORMS = ["яндекс", "2гис", "продокторов", "zoon", "google"]

# Строгая связка: «платформа: X.X★ ... (N отзывов)» в одной строке.
# Ловит ТОЛЬКО inline-формат (где рейтинг+счётчик явно привязаны к площадке).
# Stat-card (рейтинг отдельной строкой над названием) НЕ матчит → нет ложных
# срабатываний на соседние карточки разных площадок.
_INLINE_REVIEW_RE = re.compile(
    r"(яндекс|2гис|продокторов|zoon|google)\D{0,18}?"
    r"(\d[.,]\d)\s*★\D{0,45}?\(?\s*(\d{2,5})\s*отз",
    re.IGNORECASE,
)


def check_consistency(llm_text: str, formatted_blocks: list[str]) -> dict:
    """G7: рейтинг/отзывы по каждой площадке не должны противоречить сами себе.

    Проверяем только строгую inline-связку «платформа: X.X★ (N отзывов)» в
    formatted_blocks. Ловит баг «reviews: Яндекс 5.0/565 vs audit: 4.9/64»,
    не ложится на stat-card и свободный текст."""
    full = "\n".join(formatted_blocks)
    by_platform: dict[str, dict] = {}
    for m in _INLINE_REVIEW_RE.finditer(full):
        plat = m.group(1).lower()
        # нормализуем: «яндекс.карты»/«яндекс карты» → «яндекс»
        plat = re.sub(r"[.\s]*(карт|maps|бизнес|справочник).*", "", plat).strip()
        rating = normalize_num(m.group(2))
        count = m.group(3)
        d = by_platform.setdefault(plat, {"r": set(), "c": set()})
        d["r"].add(rating)
        d["c"].add(count)

    issues: list[str] = []
    for plat, d in by_platform.items():
        if len(d["r"]) > 1:
            issues.append(f"{plat}: разные рейтинги {sorted(d['r'])}")
        if len(d["c"]) > 1:
            issues.append(f"{plat}: разные кол-ва отзывов {sorted(d['c'])}")
    return {"contradictions": issues, "pass": len(issues) == 0}


# ────────────────────────────────────────────────────────────────────
# G6. COVERAGE — использует ли LLM ключевые факты из данных (полнота)
# ────────────────────────────────────────────────────────────────────
# Обратный к G1: G1 = «цифры в ответе есть в данных?» (точность)
#                G6 = «ключевые цифры из данных есть в ответе?» (полнота)
# Именно G6 ловит подавление данных (baseline: выручка 287M в данных, но не в ответе).

_REVENUE_FACT = re.compile(r"(\d[\d\s.,]*)\s*(млн|млрд)\s*₽?", re.I)


def check_coverage(llm_text: str, formatted_blocks: list[str]) -> dict:
    """G6: ключевые финансовые факты из данных упомянуты в ответе?
    Выручка/прибыль — главное, что LLM склонен подавлять."""
    corpus = "\n".join(formatted_blocks)
    text_lower = llm_text.lower()

    facts: list[str] = []
    for m in _REVENUE_FACT.finditer(corpus):
        n = normalize_num(m.group(1))
        if n and not _is_year(n):
            facts.append(n)
    # дедуп
    seen, unique = set(), []
    for f in facts:
        if f not in seen:
            seen.add(f)
            unique.append(f)

    used, missed = [], []
    for f in unique:
        if _in_corpus(f, text_lower):
            used.append(f)
        else:
            missed.append(f)

    total = len(unique)
    score = round(len(used) / total * 100, 1) if total else 100.0
    return {
        "score_pct": score,
        "total_facts": total,
        "used_count": len(used),
        "missed": missed[:10],
        "pass": score >= 50,
    }


# ────────────────────────────────────────────────────────────────────
# G5. COHERENCE — нет внутренних противоречий
# ────────────────────────────────────────────────────────────────────

_LEADER = re.compile(r"\b(лидер|лидиру|впереди|крупнейш|топ\b|первое место)", re.I)
_LOSER = re.compile(r"\b(отстае|отстаю|отстаем|аутсайдер|позади|слабее|хуже всех|недотягива)", re.I)

# Метрики, к которым привязывается позиция (выручка/прибыль/маркетинг/...).
# Если «лидер» и «отстаёт» по РАЗНЫМ метрикам — это НЕ противоречие
# («лидер по выручке, отстаёт по цифровому маркетинге» = нормальный бизнес-вывод).
_METRIC_KEYS = [
    "выруч", "прибыл", "марж", "рентабел", "доход", "эффективн", "производит",
    "маркетинг", "seo", "сайт", "цифров", "онлайн", "реклам", "техническ",
    "рейтинг", "отзыв", "репутаци", "лоял",
    "врач", "персонал", "команда", "специалист",
    "соцсет", "instagram", "вконтакте", "\\bvk\\b", "telegram",
    "услуг", "ассортим", "направлен",
    "филиал", "адрес", "локаци", "охват", "масштаб",
    "имплант", "стоматолог", "косметолог",
]
_METRIC_RE = re.compile("|".join(_METRIC_KEYS), re.I)


def _metric_near(text: str, pos: int, window: int = 22) -> str | None:
    """Найти БЛИЖАЙШУЮ метрику в малом окне (±window).
    Узкое окно = метрика относится именно к этому «лидер/отстает»."""
    # ищем в окне после слова (чаще «по ВЫРУЧКЕ», «по МАРКЕТИНГУ»)
    after = text[pos: pos + window]
    m = _METRIC_RE.search(after)
    if m:
        return m.group(0).lower()
    # реже — до слова («ВЫРУЧКА: лидер»)
    before = text[max(0, pos - window): pos]
    m = _METRIC_RE.search(before)
    return m.group(0).lower() if m else None


def check_coherence(llm_text: str) -> dict:
    """G5: «лидер» и «отстаёт» про ОДНУ И ТУ ЖЕ метрику = противоречие.
    Разные метрики («лидер по выручке, отстаёт по маркетингу») — НЕ противоречие,
    это нормальный бизнес-анализ. Без явной метрики — считаем «общая позиция»."""
    t = llm_text.lower().replace("ё", "е")
    leader_metrics: set[str] = set()
    loser_metrics: set[str] = set()
    for m in _LEADER.finditer(t):
        met = _metric_near(t, m.start())
        leader_metrics.add(met or "_общая_")
    for m in _LOSER.finditer(t):
        met = _metric_near(t, m.start())
        loser_metrics.add(met or "_общая_")

    # Противоречие = пересечение метрик (одна и та же).
    # Если есть ХОТЯ БЫ ОДНА конкретная метрика и у leader, и у loser, и они НЕ
    # пересекаются → LLM явно развёл по разным метрикам → не противоречие.
    # Флаг только если пересечение есть, либо НЕТ ни одной конкретной метрики
    # у обеих сторон (полностью общие «лидер» + «отстает» без контекста).
    common = leader_metrics & loser_metrics
    has_specific_leader = any(m != "_общая_" for m in leader_metrics)
    has_specific_loser = any(m != "_общая_" for m in loser_metrics)
    both_general = (not has_specific_leader) and (not has_specific_loser)
    contradictory = bool(common) or both_general
    return {
        "leader_metrics": sorted(x for x in leader_metrics if x != "_общая_")[:6],
        "loser_metrics": sorted(x for x in loser_metrics if x != "_общая_")[:6],
        "shared": sorted(common)[:4],
        "contradictory": contradictory,
        "pass": not contradictory,
    }


# ────────────────────────────────────────────────────────────────────
# Сводный запуск всех проверок
# ────────────────────────────────────────────────────────────────────

# [SUGGESTIONS]...[/SUGGESTIONS] — ожидаемый маркер кнопок.
# main.py парсит его в кнопки и убирает из видимого текста.
# Проверки должны работать на пользователь-видимом тексте → стрипаем.
_SUGGESTIONS_BLOCK = re.compile(
    r"\*{0,2}\[SUGGESTIONS\]\*{0,2}\s*\n?.*?\*{0,2}\[/SUGGESTIONS\]\*{0,2}",
    re.DOTALL,
)
# Citation markers [1], [2] — Perplexity-стиль, main.py их тоже убирает
_CITATIONS = re.compile(r"\[\d+\](?:\[\d+\])*")


def user_visible_text(llm_text: str) -> str:
    """Эмулирует пост-обработку main.py: убирает [SUGGESTIONS] и [1] citations."""
    t = _SUGGESTIONS_BLOCK.sub("", llm_text)
    t = _CITATIONS.sub("", t)
    return t.strip()


def run_all(snapshot: dict) -> dict:
    """Запускает G1-G5 на snapshot. Возвращает сводку.
    Проверки идут на пользователь-видимом тексте (после стрипа маркеров)."""
    events = snapshot.get("events", {})
    raw_text = events.get("llm_text", "")
    llm_text = user_visible_text(raw_text)
    formatted = events.get("formatted_blocks", [])
    tool_calls = events.get("tool_calls", [])

    return {
        "G1_grounding": check_grounding(llm_text, formatted),
        "G2_structure": check_structure(llm_text),
        "G3_clean": check_clean(llm_text),
        "G4_data": check_data_completeness(tool_calls),
        "G5_coherence": check_coherence(llm_text),
        "G6_coverage": check_coverage(llm_text, formatted),
        "G7_consistency": check_consistency(llm_text, formatted),
    }
