"""Блок «Выручка vs Конкуренты» — вау-блок в начале отчёта.

Перенесено из v1 build_report.py (строки 1327-1482) с адаптацией:
- v1 читал data["FINANCE"]["find_company_financials"] (вложенный JSON с company.latest_revenue)
- v2: client_revenue и client_profit передаются напрямую (уже извлечены в адаптере)
- Конкуренты: competitors_result — JSON-строка от find_competitors
  (та же структура competitors[].revenue_year, brand_name, inn)
"""

import json

from app.report_builder.markdown_engine import _esc, _fmt_revenue_short


def build_revenue_vs_competitors_block(
    client_revenue: float | None,
    client_profit: float | None,
    competitors_result: str,
    company_name: str,
) -> str:
    """Построить блок «Выручка vs Конкуренты» для вау-эффекта в начале отчёта.

    Args:
        client_revenue: Выручка клиента (уже извлечена из collected_results
            или profile_cache; None если данных нет).
        client_profit: Прибыль клиента (None если нет).
        competitors_result: JSON-строка от find_competitors. Ожидается структура
            ``{"competitors": [{"brand_name", "inn", "revenue_year", "revenue_trend"}]}``.
        company_name: Имя клиента (для строки «Вы» в таблице и заголовка).

    Returns:
        HTML блока или пустая строка если данных нет.
    """
    # 1. Парсим конкурентов из JSON-строки
    competitors: list = []
    if competitors_result and isinstance(competitors_result, str):
        try:
            parsed = json.loads(competitors_result)
            competitors = parsed.get("competitors", []) if isinstance(parsed, dict) else []
        except (json.JSONDecodeError, TypeError):
            competitors = []
    elif isinstance(competitors_result, list):
        # На случай если передали уже распарсенный список
        competitors = competitors_result
    elif isinstance(competitors_result, dict):
        competitors = competitors_result.get("competitors", [])

    # Оставляем только конкурентов с реальной выручкой
    competitors_with_rev = [
        c for c in competitors
        if isinstance(c, dict) and c.get("revenue_year") and c.get("revenue_year") > 0
    ]

    if not client_revenue and not competitors_with_rev:
        return ""

    # Тренд клиента: в v2 он не передаётся напрямую (оставлено для совместимости)
    client_trend = None

    # 2. Сортируем по убыванию выручки — клиент + конкуренты вместе
    all_rows = []
    if client_revenue:
        all_rows.append({
            "name": company_name,
            "is_client": True,
            "revenue": client_revenue,
            "trend": client_trend,
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

    # Парсим trend → emoji/цвет
    def _trend_marker(t):
        if not t:
            return ("—", "")
        t_lower = str(t).lower()
        if "grow" in t_lower or t_lower == "растущий":
            return ("▲", "trend-up")
        if "declining" in t_lower or "fall" in t_lower or "пад" in t_lower:
            return ("▼", "trend-down")
        if "stable" in t_lower or "стаб" in t_lower:
            return ("▬", "trend-stable")
        return ("—", "")

    # Считаем VAU-инсайт: кратность лидера к ближайшему конкуренту
    wow_html = ""
    if client_revenue and len(competitors_with_rev) > 0:
        top_comp_revenue = max(c.get("revenue_year", 0) for c in competitors_with_rev)
        if top_comp_revenue > 0:
            ratio = client_revenue / top_comp_revenue
            if ratio >= 1.2 and client_position == 1:
                wow_html = (
                    f'<div class="wow-banner">'
                    f'<strong>ВАУ:</strong> {_esc(company_name)} в '
                    f'<strong>{ratio:.1f} раза</strong> больше ближайшего конкурента.'
                    f'</div>'
                )

    # Строим таблицу
    rows_html = []
    for i, row in enumerate(all_rows, 1):
        revenue_str = _fmt_revenue_short(row["revenue"])
        trend_emoji, trend_class = _trend_marker(row["trend"])
        client_class = " row-client" if row["is_client"] else ""
        rank_class = (
            " rank-gold" if i == 1
            else (" rank-silver" if i == 2
                  else (" rank-bronze" if i == 3 else ""))
        )
        rows_html.append(
            f'<tr class="comp-row{client_class}">'
            f'<td class="comp-rank{rank_class}">{i}</td>'
            f'<td class="comp-name">{_esc(row["name"])}</td>'
            f'<td class="comp-revenue">{revenue_str}</td>'
            f'<td class="comp-trend {trend_class}">{trend_emoji}</td>'
            f'</tr>'
        )
    rows_html_str = "".join(rows_html)

    # Если клиент не найден — показываем только конкурентов
    title_str = (
        f"{company_name} vs {len(competitors_with_rev)} главных конкурента"
        if client_revenue
        else f"Топ-{len(competitors_with_rev)} конкурентов {company_name}"
    )

    subtitle = ""
    if client_revenue and client_position == 1 and len(competitors_with_rev) >= 2:
        subtitle = "Лидер рынка. Выручка 2025 по данным ФНС."
    elif client_revenue and client_position:
        subtitle = f"{client_position}-е место среди сравниваемых клиник. Выручка 2025 по данным ФНС."
    else:
        subtitle = "Выручка конкурентов 2025 по данным ФНС (bo.nalog.gov.ru)."

    # profit не отображается в этом блоке отдельно (клиент = в общей таблице),
    # но логируем доступность для будущих расширений.
    _ = client_profit

    return f"""
<section class="revenue-block">
  <span class="sec-tag sec-tag-highlight">СРАВНЕНИЕ С КОНКУРЕНТАМИ</span>
  <h2>{_esc(title_str)}</h2>
  <p class="text-dim">{_esc(subtitle)}</p>
  {wow_html}
  <table class="comp-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Клиника</th>
        <th>Выручка</th>
        <th>Тренд</th>
      </tr>
    </thead>
    <tbody>
      {rows_html_str}
    </tbody>
  </table>
  <p class="text-dim comp-source">Источник: ФНС, bo.nalog.gov.ru (налоговая отчётность)</p>
</section>
"""
