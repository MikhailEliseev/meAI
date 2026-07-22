"""HTML report builder — v2 перенос из v1 build_report.py.

Публичный API:
- build_report_html(data, title) — сборка финального HTML
- build_data_dict(collected_results, profile_cache, llm_text) — адаптер v2 → v1-shape
"""

from app.report_builder.builder import build_report_html
from app.report_builder.adapter import build_data_dict

__all__ = ["build_report_html", "build_data_dict"]
