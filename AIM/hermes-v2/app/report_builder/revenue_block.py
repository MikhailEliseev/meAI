"""Блок «Выручка vs Конкуренты» — минималистичный стиль чата.

Переделано из v1-стиля (большие .comp-table с золотыми рангами) под
дизайн-систему: простая таблица как в чате (border-collapse, тонкие бордеры,
компактный padding), плюс акцентная подсветка строки клиента.

Совпадает с CSS таблиц в chat-inline.php (.message-bubble table).
"""

import json

from app.report_builder.markdown_engine import _esc, _fmt_revenue_short


# ── Форматтеры доп. колонок (Задача 3) ──────────────────────────────────────────

def _fmt_age(reg_date) -> str:
    """'2018-06-15' → '8 лет'. None → '—'."""
    if not reg_date:
        return "—"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(str(reg_date)[:10])
        years = (datetime.now() - dt).days // 365
        return f"{years} лет" if years > 0 else "—"
    except (ValueError, TypeError):
        return "—"


def _fmt_followers(val) -> str:
    """31000 → '31K'. None → '—'."""
    if not val:
        return "—"
    try:
        n = int(val)
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n//1_000}K"
        return str(n)
    except (ValueError, TypeError):
        return "—"


def _fmt_profit(val) -> str:
    """3_000_000 → '3 млн'. None → '—'."""
    if not val:
        return "—"
    try:
        n = float(val)
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f} млрд"
        if n >= 1_000_000:
            return f"{n/1_000_000:.0f} млн"
        return f"{n:,.0f}".replace(",", " ")
    except (ValueError, TypeError):
        return "—"



# ── Очистка данных конкурентов ─────────────────────────────────────────────────
# Защита от мусора, который утекает из Perplexity-парсера aim-app:
#   - LLM-болтовня в brand_name ("Вот несколько известных клиник...")
#   - дубликаты одной компании с разной выручкой (разные ИНН-lookup'ы)

# Фразы-маркеры болтовни LLM (не реальные бренды)
_CHATTER_WORDS = (
    "вот ", "например", "известных", "таких как", "также ", "перейдём",
    "перейдем", "итак", "также,", "однако", "итого", "итак,", "наконец",
    "среди них", "список", "обратите", "стоит отметить", "важно ",
)


def _is_valid_brand(brand: str) -> bool:
    """Проверить, что имя выглядит как реальный бренд, а не LLM-болтовня."""
    if not brand or len(brand) < 2:
        return False
    brand = brand.strip().strip('"').strip("'")
    # Слишком длинное имя — не бренд (реальные бренды ≤ 60 символов)
    if len(brand) > 60:
        return False
    # Двоеточие в конце/середине — признак болтовни ("Вот несколько...:")
    if ":" in brand or brand.endswith(":"):
        return False
    # Маркеры болтовни
    brand_lower = brand.lower()
    for word in _CHATTER_WORDS:
        if word in brand_lower:
            return False
    # 5+ слов подряд — почти наверняка предложение, не бренд
    if len(brand.split()) > 4:
        return False
    return True


def _clean_competitors(competitors: list) -> list:
    """Отфильтровать мусор и дедуплицировать список конкурентов.

    1. Убрать конкурентов с мусорными именами (_is_valid_brand).
    2. Дедупликация: приоритет по ИНН (разные ИНН = разные юрлица, оставляем),
       fallback по нормализованному имени (ООО "ЭСТЕТ" == ООО «ЭСТЕТ»).
    3. При дубликате по имени — оставить запись с большей выручкой.
    """
    # 1. Фильтр мусорных имён
    valid = []
    for c in competitors:
        brand = c.get("brand_name") or c.get("legal_name") or ""
        if _is_valid_brand(brand):
            valid.append(c)

    # 2. Дедупликация (приоритет ИНН, fallback — имя)
    seen_keys: dict[str, dict] = {}  # key → best competitor
    for c in valid:
        inn = str(c.get("inn", "") or "").strip()
        brand = (c.get("brand_name") or c.get("legal_name") or "").strip()
        # Нормализованное имя: нижний регистр, убрать кавычки/пробелы/ООО/пунктуацию
        name_norm = brand.lower()
        for ch in ('"', "'", "«", "»", ".", ",", " "):
            name_norm = name_norm.replace(ch, "")
        for prefix in ("ооо", "зао", "ао", "ип", "пао"):
            if name_norm.startswith(prefix):
                name_norm = name_norm[len(prefix):]

        # Ключ дедупликации: ИНН если валиден, иначе нормализованное имя
        if inn and inn != "0" and len(inn) >= 10:
            key = f"inn:{inn}"
        elif name_norm and len(name_norm) >= 3:
            key = f"name:{name_norm}"
        else:
            # Нет ни ИНН, ни внятного имени — пропускаем (не дедуплицируем,
            # но такие записи уже отфильтрованы _is_valid_brand выше)
            key = f"raw:{id(c)}"

        rev = c.get("revenue_year", 0) or 0
        if key not in seen_keys or rev > (seen_keys[key].get("revenue_year", 0) or 0):
            seen_keys[key] = c

    return list(seen_keys.values())



def build_revenue_vs_competitors_block(
    client_revenue: float | None,
    client_profit: float | None,
    competitors_result: str,
    company_name: str,
) -> str:
    """Построить блок «Выручка vs Конкуренты» — минималистичный стиль чата.

    Args:
        client_revenue: Выручка клиента (None если данных нет).
        client_profit: Прибыль клиента (None если нет).
        competitors_result: JSON-строка от find_competitors.
        company_name: Имя клиента.

    Returns:
        HTML блока или пустая строка если данных нет.
    """
    # 1. Парсим конкурентов
    competitors: list = []
    if competitors_result and isinstance(competitors_result, str):
        try:
            parsed = json.loads(competitors_result)
            competitors = parsed.get("competitors", []) if isinstance(parsed, dict) else []
        except (json.JSONDecodeError, TypeError):
            competitors = []
    elif isinstance(competitors_result, list):
        competitors = competitors_result
    elif isinstance(competitors_result, dict):
        competitors = competitors_result.get("competitors", [])

    competitors_with_rev = [
        c for c in competitors
        if isinstance(c, dict) and c.get("revenue_year") and c.get("revenue_year") > 0
    ]

    # ── Очистка конкурентов (Fix 2+3) ──────────────────────────────────────────
    # Фильтр мусорных имён (LLM-болтовня, утекшая в brand_name из Perplexity) +
    # дедупликация по ИНН (приоритет) или по нормализованному имени.
    competitors_with_rev = _clean_competitors(competitors_with_rev)

    if not client_revenue and not competitors_with_rev:
        return ""

    # 2. Сортируем по убыванию выручки — клиент + конкуренты вместе
    all_rows = []
    if client_revenue:
        all_rows.append({
            "name": company_name,
            "is_client": True,
            "revenue": client_revenue,
            "trend": None,
            "inn": None,
            "profit": client_profit,
            "age": "—",
            "instagram": "—",
            "doctors": None,
            "cms": "",
        })
    for c in competitors_with_rev:
        brand = c.get("brand_name") or c.get("legal_name") or "Конкурент"
        all_rows.append({
            "name": brand,
            "is_client": False,
            "revenue": c.get("revenue_year", 0),
            "trend": c.get("revenue_trend"),
            "inn": c.get("inn", ""),
            # Доп. данные для обогащённой таблицы (Задача 3)
            "profit": c.get("profit_year"),
            "age": _fmt_age(c.get("registration_date")),
            "instagram": _fmt_followers(c.get("instagram_followers")),
            "doctors": c.get("surgeons_count") or c.get("employee_count"),
            "cms": c.get("website_cms") or "",
        })
    all_rows.sort(key=lambda r: r["revenue"], reverse=True)

    # ── Disambiguation: одинаковые имена, разные ИНН (Fix Баг 3 v2) ─────────────
    # Если два конкурента с одинаковым именем но разными ИНН (реально разные
    # юрлица — «ООО ЭСТЕТ» №1 и №2), добавляем различающий суффикс с ИНН,
    # чтобы в таблице не было визуально идентичных строк.
    name_inn_groups: dict[str, list[int]] = {}  # name → list of row indices
    for i, row in enumerate(all_rows):
        if not row["is_client"]:
            name_inn_groups.setdefault(row["name"], []).append(i)
    for name, indices in name_inn_groups.items():
        if len(indices) < 2:
            continue
        # Проверяем что ИНН действительно разные
        inns = {all_rows[idx]["inn"] for idx in indices}
        if len(inns) < 2:
            continue  # одинаковые ИНН — _clean_competitors уже дедуплицировал
        # Добавляем суффикс «… ИНН …XXXX» к каждой строке с этим именем
        for idx in indices:
            inn = all_rows[idx]["inn"]
            if inn and len(str(inn)) >= 4:
                suffix = f" (ИНН …{str(inn)[-4:]})"
                all_rows[idx]["name"] = name + suffix


    # VAU-блок: позиция клиента
    client_position = next(
        (i + 1 for i, r in enumerate(all_rows) if r["is_client"]),
        None,
    )

    # Парсим trend → символ/цвет
    def _trend_marker(t):
        if not t:
            return ("", "")
        t_lower = str(t).lower()
        if "grow" in t_lower or t_lower == "растущий":
            return ("▲", "rev-trend-up")
        if "declining" in t_lower or "fall" in t_lower or "пад" in t_lower:
            return ("▼", "rev-trend-down")
        if "stable" in t_lower or "стаб" in t_lower:
            return ("▬", "rev-trend-stable")
        return ("", "")

    # VAU-инсайт: кратность лидера к ближайшему конкуренту
    wow_html = ""
    if client_revenue and len(competitors_with_rev) > 0:
        top_comp_revenue = max(c.get("revenue_year", 0) for c in competitors_with_rev)
        if top_comp_revenue > 0:
            ratio = client_revenue / top_comp_revenue
            if ratio >= 1.2 and client_position == 1:
                wow_html = (
                    f'<div class="rev-wow">'
                    f'<strong>ВАУ:</strong> {_esc(company_name)} в '
                    f'<strong>{ratio:.1f} раза</strong> больше ближайшего конкурента.'
                    f'</div>'
                )

    # Строим таблицу — обогащённая (Задача 3: доп. колонки)
    rows_html = []
    for i, row in enumerate(all_rows, 1):
        revenue_str = _fmt_revenue_short(row["revenue"])
        trend_symbol, trend_class = _trend_marker(row["trend"])
        client_class = " rev-row-client" if row["is_client"] else ""
        trend_html = (
            f'<span class="rev-trend {trend_class}">{trend_symbol}</span>'
            if trend_symbol else '<span class="rev-trend">—</span>'
        )
        profit_str = _fmt_profit(row.get("profit")) if not row["is_client"] else _fmt_profit(client_profit)
        doctors_str = str(row.get("doctors")) if row.get("doctors") else "—"
        rows_html.append(
            f'<tr class="rev-row{client_class}">'
            f'<td class="rev-position">{i}</td>'
            f'<td class="rev-name">{_esc(row["name"])}</td>'
            f'<td class="rev-revenue">{revenue_str}</td>'
            f'<td class="rev-th-num">{profit_str}</td>'
            f'<td class="rev-trend-cell">{trend_html}</td>'
            f'<td class="rev-th-num">{_esc(row.get("age", "—"))}</td>'
            f'<td class="rev-th-num">{_esc(doctors_str)}</td>'
            f'<td class="rev-th-num">{_esc(row.get("instagram", "—"))}</td>'
            f'</tr>'
        )
    rows_html_str = "".join(rows_html)

    title_str = (
        f"{company_name} vs {len(competitors_with_rev)} главных конкурентов"
        if client_revenue
        else f"Топ-{len(competitors_with_rev)} конкурентов {company_name}"
    )

    if client_revenue and client_position == 1 and len(competitors_with_rev) >= 2:
        subtitle = "Лидер рынка. Выручка 2025 по данным ФНС."
    elif client_revenue and client_position:
        subtitle = f"{client_position}-е место среди сравниваемых клиник. Выручка 2025 по данным ФНС."
    else:
        subtitle = "Выручка конкурентов 2025 по данным ФНС (bo.nalog.gov.ru)."

    return f"""
<section class="revenue-block">
  <div class="rev-section-label">СРАВНЕНИЕ С КОНКУРЕНТАМИ</div>
  <h2>{_esc(title_str)}</h2>
  <p class="rev-subtitle">{_esc(subtitle)}</p>
  {wow_html}
  <div class="rev-table-wrap">
    <table>
      <thead>
        <tr>
          <th class="rev-th-pos">#</th>
          <th>Клиника</th>
          <th class="rev-th-num">Выручка</th>
          <th class="rev-th-num">Прибыль</th>
          <th class="rev-th-num">Тренд</th>
          <th class="rev-th-num">Лет</th>
          <th class="rev-th-num">Врачей</th>
          <th class="rev-th-num">IG</th>
        </tr>
      </thead>
      <tbody>
        {rows_html_str}
      </tbody>
    </table>
  </div>
  <p class="rev-source">Источник: ФНС, bo.nalog.gov.ru</p>
</section>
"""
