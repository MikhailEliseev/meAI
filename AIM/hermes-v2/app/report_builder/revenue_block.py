"""Блок «Выручка vs Конкуренты» — минималистичный стиль чата.

Переделано из v1-стиля (большие .comp-table с золотыми рангами) под
дизайн-систему: простая таблица как в чате (border-collapse, тонкие бордеры,
компактный padding), плюс акцентная подсветка строки клиента.

Совпадает с CSS таблиц в chat-inline.php (.message-bubble table).
"""

import json

from app.report_builder.markdown_engine import _esc, _fmt_revenue_short


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
        })
    for c in competitors_with_rev:
        brand = c.get("brand_name") or c.get("legal_name") or "Конкурент"
        all_rows.append({
            "name": brand,
            "is_client": False,
            "revenue": c.get("revenue_year", 0),
            "trend": c.get("revenue_trend"),
            "inn": c.get("inn", ""),
        })
    all_rows.sort(key=lambda r: r["revenue"], reverse=True)

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

    # Строим таблицу — простой минималистичный стиль как в чате
    # БЕЗ медальности (ранги #1/2/3 без золотого/серебряного/бронзового цвета)
    rows_html = []
    for i, row in enumerate(all_rows, 1):
        revenue_str = _fmt_revenue_short(row["revenue"])
        trend_symbol, trend_class = _trend_marker(row["trend"])
        client_class = " rev-row-client" if row["is_client"] else ""
        trend_html = (
            f'<span class="rev-trend {trend_class}">{trend_symbol}</span>'
            if trend_symbol else '<span class="rev-trend">—</span>'
        )
        rows_html.append(
            f'<tr class="rev-row{client_class}">'
            f'<td class="rev-position">{i}</td>'
            f'<td class="rev-name">{_esc(row["name"])}</td>'
            f'<td class="rev-revenue">{revenue_str}</td>'
            f'<td class="rev-trend-cell">{trend_html}</td>'
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

    _ = client_profit  # зарезервировано для будущих расширений

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
          <th class="rev-th-num">Тренд</th>
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
