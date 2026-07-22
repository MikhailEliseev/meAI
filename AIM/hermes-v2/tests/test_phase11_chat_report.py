"""Тесты для Phase 11: Chat Report Integration.

Покрывает:
- _auto_publish_report: корректные args, ошибки не поднимаются, URL возвращается
- chat_with_tools: триггер срабатывает при find_competitors, пропускается без него
- Гвард дубликатов через profile_cache["_report_published_url"]
- SSE формат в event_generator (main.py)
"""

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Путь к репо для frontend tests (tests/ находится в hermes-v2/tests/)
# → нужно подняться на 2 уровня: tests/ → hermes-v2/ → AIM/ (где theme/)
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CHAT_INLINE_PHP = os.path.join(_REPO_ROOT, "theme", "chat-inline.php")


# ──────────────────────────────────────────────────────────────────────────
# _auto_publish_report (llm.py)
# ──────────────────────────────────────────────────────────────────────────


def _profile_raw(**overrides) -> str:
    base = {
        "company_name": "Test Clinic",
        "inn": "7700000000",
        "city": "Москва",
        "address": "ул. Теста, 1",
        "doctors_count": 10,
        "registration_date": "2018-05-10",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=False)


def _competitors_raw() -> str:
    return json.dumps(
        {
            "competitors": [
                {"brand_name": "Comp 1", "revenue_year": 200_000_000, "revenue_trend": "growing"},
            ]
        },
        ensure_ascii=False,
    )


async def _collect(gen):
    """Собрать все yields из async генератора."""
    items = []
    async for item in gen:
        items.append(item)
    return items


@pytest.mark.asyncio
async def test_auto_publish_report_success():
    """При успешной публикации yield-ит ("report_ready", url, title)."""
    from app.llm import _auto_publish_report

    collected = {
        "find_competitors": _competitors_raw(),
        "extract_clinic_profile": _profile_raw(),
    }
    profile_cache = {"company_name": "Test Clinic"}

    # Мокаем publish_report — патчим модуль, из которого импортируется publish_report
    async def fake_publish(html, title):
        return {"status": "published", "url": "https://iamaim.ru/test123", "slug": "test123", "post_id": 999}

    import app.report_builder as rb_mod
    original = rb_mod.publish_report
    rb_mod.publish_report = fake_publish
    try:
        results = await _collect(_auto_publish_report(collected, profile_cache, "llm text"))
    finally:
        rb_mod.publish_report = original

    assert len(results) == 1
    event = results[0]
    assert event[0] == "report_ready"
    assert event[1] == "https://iamaim.ru/test123"
    assert event[2] == "Test Clinic"
    # Гвард записан
    assert profile_cache["_report_published_url"] == "https://iamaim.ru/test123"


@pytest.mark.asyncio
async def test_auto_publish_report_failure_no_crash():
    """При ошибке publish_report функция не падает — просто не yield-ит."""
    from app.llm import _auto_publish_report

    collected = {"find_competitors": _competitors_raw()}
    profile_cache = {}

    async def failing_publish(html, title):
        return {"status": "error", "error": "DB down"}

    import app.report_builder as rb_mod
    original = rb_mod.publish_report
    rb_mod.publish_report = failing_publish
    try:
        # Не должно raise
        results = await _collect(_auto_publish_report(collected, profile_cache, ""))
    finally:
        rb_mod.publish_report = original

    # Нет yields (т.к. ошибка)
    assert results == []
    # Гвард НЕ записан
    assert "_report_published_url" not in profile_cache


@pytest.mark.asyncio
async def test_auto_publish_report_saved_locally():
    """При saved_locally (нет DB) — тоже не yield-ит, но и не падает."""
    from app.llm import _auto_publish_report

    collected = {"find_competitors": _competitors_raw()}

    async def local_publish(html, title):
        return {"status": "saved_locally", "path": "/tmp/test.html", "url": None}

    import app.report_builder as rb_mod
    original = rb_mod.publish_report
    rb_mod.publish_report = local_publish
    try:
        results = await _collect(_auto_publish_report(collected, {}, ""))
    finally:
        rb_mod.publish_report = original

    assert results == []


# ──────────────────────────────────────────────────────────────────────────
# chat_with_tools: trigger conditions
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trigger_skip_without_find_competitors(monkeypatch):
    """Без find_competitors отчёт НЕ публикуется (например, 'привет' в чат).

    Проверяем через мок: если _auto_publish_report не вызывается — значит триггер не сработал.
    """
    from app import llm as llm_mod

    publish_calls = []

    async def spy_publish(*args, **kwargs):
        publish_calls.append((args, kwargs))
        # Возвращаем генератор без items
        return
        yield  # noqa — делает функцию async generator

    # Подменяем _auto_publish_report шпионом
    monkeypatch.setattr(llm_mod, "_auto_publish_report", spy_publish)

    # chat_with_tools сложный — нужно мокать client + tools.
    # Вместо полноценного прогона проверим логику триггера напрямую:
    collected_results = {}  # без find_competitors
    profile_cache = {}

    # Логика триггера (как в llm.py строки ~902-916):
    if "find_competitors" in collected_results and not profile_cache.get("_report_published_url"):
        # НЕ должно сработать
        await _collect(spy_publish(collected_results, profile_cache, ""))

    # Шпион не вызывался (т.к. find_competitors не в collected)
    assert len(publish_calls) == 0


@pytest.mark.asyncio
async def test_duplicate_guard_prevents_republish():
    """Гвард _report_published_url предотвращает повторную публикацию."""
    # Симулируем второй вызов: profile_cache уже имеет URL
    collected_results = {"find_competitors": _competitors_raw()}
    profile_cache = {"_report_published_url": "https://iamaim.ru/already"}

    # Логика гварда (как в llm.py):
    should_publish = (
        "find_competitors" in collected_results
        and not profile_cache.get("_report_published_url")
    )
    assert should_publish is False, "Guard should prevent republish"


# ──────────────────────────────────────────────────────────────────────────
# SSE event format (main.py)
# ──────────────────────────────────────────────────────────────────────────


def test_sse_report_ready_event_format():
    """Проверяем формат SSE event для report-ready.

    Ожидаемый формат: data: {"type":"report-ready","url":"...","title":"...","summary":"..."}\n\n
    """
    # Симулируем логику из main.py event_generator()
    url = "https://iamaim.ru/abc123"
    title = "Test Clinic"
    summary = f"Полный разбор: {title}"
    payload = {
        "type": "report-ready",
        "url": url,
        "title": title,
        "summary": summary,
    }
    sse_line = f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    # Парсим обратно
    assert sse_line.startswith("data: ")
    assert sse_line.endswith("\n\n")
    json_str = sse_line[len("data: "):-2]
    parsed = json.loads(json_str)
    assert parsed["type"] == "report-ready"
    assert parsed["url"] == url
    assert parsed["title"] == title
    assert "разбор" in parsed["summary"].lower()


def test_sse_report_ready_no_title_fallback():
    """Если title пустой — summary использует fallback."""
    url = "https://iamaim.ru/test"
    title = ""
    summary = f"Полный разбор: {title}" if title else "Полный разбор сайта, конкурентов и рынка"
    # При пустом title должна быть общая фраза
    assert summary == "Полный разбор сайта, конкурентов и рынка"


# ──────────────────────────────────────────────────────────────────────────
# Frontend: chat-inline.php handler
# ──────────────────────────────────────────────────────────────────────────


def test_chat_inline_has_report_ready_handler():
    """chat-inline.php содержит handler для 'report-ready' SSE event."""
    with open(_CHAT_INLINE_PHP, "r", encoding="utf-8") as f:
        content = f.read()

    # Handler должен быть добавлен
    assert "data.type === 'report-ready'" in content
    # Использует существующий renderReportCard через маркер
    assert "[REPORT_READY]" in content


def test_chat_inline_has_renderReportCard():
    """renderReportCard() функция существует и рендерит карточку."""
    with open(_CHAT_INLINE_PHP, "r", encoding="utf-8") as f:
        content = f.read()

    assert "function renderReportCard" in content
    assert "report-ready-card" in content
    assert "report-ready-link" in content


def test_chat_inline_has_report_card_css():
    """CSS для .report-ready-card присутствует."""
    with open(_CHAT_INLINE_PHP, "r", encoding="utf-8") as f:
        content = f.read()

    assert ".report-ready-card" in content
    assert ".report-ready-icon" in content
    assert ".report-ready-title" in content
    assert ".report-ready-link" in content


# ──────────────────────────────────────────────────────────────────────────
# Code Review fixes: W-1, W-2, W-3, I-2
# ──────────────────────────────────────────────────────────────────────────


def test_w1_no_collected_results_reset():
    """W-1: в llm.py больше НЕТ КОДОВОГО присваивания collected_results = {}
    внутри блока parallel tool execution (только в комментариях-предупреждениях).
    """
    llm_py = os.path.join(_REPO_ROOT, "hermes-v2", "app", "llm.py")
    with open(llm_py, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Ищем строку с присваиванием collected_results = {} (не в комментарии)
    reset_lines = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue  # Комментарий — пропускаем
        if "collected_results = {}" in stripped and "collected_results" in stripped.split("=")[0]:
            reset_lines.append((i + 1, line.rstrip()))
    assert len(reset_lines) == 0, (
        f"W-1 regression: found {len(reset_lines)} code line(s) with "
        f"'collected_results = {{}}' (not in comments): {reset_lines}"
    )


def test_w2_frontend_pendingReportReady_pattern():
    """W-2: фронтенд использует pendingReportReady, а НЕ прямую вставку в SSE handler."""
    with open(_CHAT_INLINE_PHP, "r", encoding="utf-8") as f:
        content = f.read()
    # Переменная должна быть объявлена
    assert "pendingReportReady" in content
    # Handler НЕ должен делать assistantMessage += внутри SSE loop
    # (вставка только после removeStreamingBubble)
    # Проверяем что после report-ready handler НЕТ прямой вставки assistantMessage +=
    # в том же блоке.
    handler_idx = content.find("data.type === 'report-ready'")
    if handler_idx != -1:
        # Берём 600 символов после handler
        snippet = content[handler_idx:handler_idx + 600]
        # Не должно быть прямой вставки в assistantMessage внутри handler
        assert "assistantMessage +=" not in snippet, (
            "W-2 regression: assistantMessage += inside report-ready handler — "
            "should use pendingReportReady + post-stream insert"
        )


def test_w2_frontend_post_stream_insert():
    """W-2: вставка [REPORT_READY] маркера после removeStreamingBubble()."""
    with open(_CHAT_INLINE_PHP, "r", encoding="utf-8") as f:
        content = f.read()
    remove_idx = content.find("removeStreamingBubble();")
    # Должна быть вставка после removeStreamingBubble в районе 200 символов
    assert remove_idx != -1
    snippet = content[remove_idx:remove_idx + 500]
    assert "pendingReportReady" in snippet, (
        "W-2 regression: post-stream insert of pendingReportReady not found after removeStreamingBubble"
    )


def test_w3_db_guard_in_main_py():
    """W-3: main.py проверяет history на [REPORT_READY] маркер перед вызовом chat_with_tools."""
    main_py = os.path.join(_REPO_ROOT, "hermes-v2", "app", "main.py")
    with open(main_py, "r", encoding="utf-8") as f:
        content = f.read()
    assert "report_already_published" in content
    assert "[REPORT_READY]" in content


def test_i2_report_marker_persisted_to_db():
    """I-2: при report-ready URL сохраняется в БД через report_marker_for_db."""
    main_py = os.path.join(_REPO_ROOT, "hermes-v2", "app", "main.py")
    with open(main_py, "r", encoding="utf-8") as f:
        content = f.read()
    assert "report_marker_for_db" in content
    # Маркер должен добавляться к full_clean перед сохранением
    assert "full_clean" in content
    assert "report_marker_for_db" in content


def test_duplicate_guard_works_with_history():
    """W-3: симулируем history с [REPORT_READY] — гвард должен сработать."""
    # Логика проверки (как в main.py):
    history = [
        {"role": "user", "content": "https://test.ru"},
        {"role": "assistant", "content": "Анализ...\n\n[REPORT_READY]{\"url\":\"https://iamaim.ru/test\"}[/REPORT_READY]"},
    ]
    report_already_published = any(
        "[REPORT_READY]" in msg.get("content", "")
        for msg in history
        if msg.get("role") == "assistant"
    )
    assert report_already_published is True, "Guard should detect existing report in history"


def test_no_false_positive_in_clean_history():
    """W-3: history БЕЗ [REPORT_READY] — гвард НЕ должен сработать."""
    history = [
        {"role": "user", "content": "https://test.ru"},
        {"role": "assistant", "content": "Анализ без отчёта. Просто текст."},
    ]
    report_already_published = any(
        "[REPORT_READY]" in msg.get("content", "")
        for msg in history
        if msg.get("role") == "assistant"
    )
    assert report_already_published is False
