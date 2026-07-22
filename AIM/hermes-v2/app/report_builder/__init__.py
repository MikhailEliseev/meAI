"""HTML report builder + publisher — v2 перенос из v1.

Публичный API:
- build_report_html(data, title) — сборка финального HTML (Phase 9)
- build_data_dict(collected_results, profile_cache, llm_text) — адаптер v2 → v1-shape (Phase 9)
- publish_report(html, title) — публикация в WordPress (Phase 10)
"""

from app.report_builder.builder import build_report_html
from app.report_builder.adapter import build_data_dict
from app.report_builder.publisher import publish_report

__all__ = ["build_report_html", "build_data_dict", "publish_report"]
