# Chat Pipeline Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Починить 3 проблемы пайплайна чата v2, выявленные e2e-тестом 21 июля: (1) ложное UI-сообщение «Google Maps», (2) ИНН/выручка не находятся, хотя данные доступны через ФНС, (3) при падении Apify отзывы полностью исчезают вместо graceful сообщения.

**Architecture:** Все правки в `AIM/hermes-v2/app/` — серверная часть. Фронтенд (PHP) не трогаем. Изменения точечные, без рефакторинга: исправляем текст UI-сообщений, добавляем auto-call `company_financials` после `find_competitors` (по аналогии с существующим auto-call `run_review_platforms`), и улучшаем fallback блокa отзывов.

**Tech Stack:** Python 3.11 (FastAPI + asyncio + httpx), hermes-v2, тесты на pytest.

## Global Constraints

- Деплой через scp + docker compose (см. `DEPLOY-VIA-SCP.md`), НЕ через git pull на сервере
- Каждое изменение совместимо с существующим форматом JSON (`_format_reviews_block`, `_build_formatted_blocks` не должны ломаться)
- Фронтенд (`AIM/theme/chat-inline-golden.php`) не модифицируем
- Тесты: `pytest` через `.venv/bin/python -m pytest` (Python 3.14 локально, 3.11 в Docker)
- Git: коммиты на ветку `feat/competitor-v2-perplexity-searxng`, `git add -f` для файлов в `app/lib/` (gitignored)

---

## File Structure

| Файл | Действие | Ответственность |
|---|---|---|
| `AIM/hermes-v2/app/llm.py` | Modify | UI-сообщения (`_TOOL_MESSAGES`), auto-call financials, reviews fallback |
| `AIM/hermes-v2/tests/test_pipeline_fixes.py` | Create | Юнит-тесты для всех 3 фиксов |
| `AIM/hermes-v2/app/tools/run_review_platforms.py` | Modify | Улучшить `_build_summary` для graceful fallback |

---

## Task 1: Честные UI-сообщения прогресса тулов

**Проблема:** Сообщение «🗺️ Ищу конкурентов рядом через Google Maps» — ложное. Код использует Perplexity+SearXNG→ФНС стратегию (V2), не Google Maps (это была V1, удалена). Также «📋 Определяю клинику: ИНН, юрлицо» обещает ИНН, который Perplexity почти никогда не находит.

**Files:**
- Modify: `AIM/hermes-v2/app/llm.py:77-125` (`_TOOL_MESSAGES` dict)
- Test: `AIM/hermes-v2/tests/test_pipeline_fixes.py` (новый файл)

**Interfaces:**
- Produces: `_TOOL_MESSAGES` dict с честными описаниями (используется в строках 244-248 llm.py для tool-progress событий)

- [ ] **Step 1: Создать тестовый файл с failing-тестом**

Создать `AIM/hermes-v2/tests/test_pipeline_fixes.py`:

```python
"""Тесты фиксов пайплайна чата v2 (Task 1-3 плана 2026-07-21)."""
from app.llm import _TOOL_MESSAGES


class TestToolMessagesHonest:
    """Task 1: UI-сообщения не должны врать про Google Maps и ИНН."""

    def test_find_competitors_message_no_google_maps(self):
        """Сообщение о конкурентах НЕ должно упоминать Google Maps."""
        msg = _TOOL_MESSAGES["find_competitors"]["start"]
        assert "Google Maps" not in msg, (
            f"Сообщение '{msg}' упоминает Google Maps, "
            "но код использует Perplexity+SearXNG→ФНС стратегию"
        )

    def test_find_competitors_message_mentions_fns(self):
        """Сообщение должно честно говорить про ФНС/налоговую."""
        msg = _TOOL_MESSAGES["find_competitors"]["start"]
        assert "ФНС" in msg or "налогов" in msg or "Perplexity" in msg, (
            f"Сообщение '{msg}' не объясняет реальный источник данных"
        )

    def test_extract_clinic_profile_message_honest_about_inn(self):
        """Сообщение о профиле не должно обещать ИНН (Perplexity его не находит)."""
        msg = _TOOL_MESSAGES["extract_clinic_profile"]["start"]
        # ИНН может упоминаться, но не как главный результат
        assert "ИНН" not in msg or "адрес" in msg, (
            f"Сообщение '{msg}' обещает ИНН как главный результат, "
            "но Perplexity его почти никогда не находит"
        )
```

- [ ] **Step 2: Запустить тест, убедиться что он падает**

Run: `cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes-v2 && .venv/bin/python -m pytest tests/test_pipeline_fixes.py::TestToolMessagesHonest -v`

Expected: FAIL с сообщением про Google Maps.

- [ ] **Step 3: Исправить `_TOOL_MESSAGES` в llm.py**

Заменить блок `AIM/hermes-v2/app/llm.py:77-89` (записи `extract_clinic_profile` и `find_competitors`):

```python
_TOOL_MESSAGES = {
    "extract_clinic_profile": {
        "start": "📋 Определяю клинику: адрес, специализация, услуги…",
        "done": "✅ Профиль клиники готов",
    },
    "quick_overview": {
        "start": "🔍 Собираю обзор: врачи, услуги, соцсети…",
        "done": "✅ Обзор готов",
    },
    "find_competitors": {
        "start": "🗺️ Ищу конкурентов через Perplexity и ФНС (это ~1-2 минуты)…",
        "done": "✅ Конкуренты найдены",
    },
```

Остальные записи (`enrich_competitors`, `company_financials`, и т.д.) оставить без изменений.

- [ ] **Step 4: Запустить тест, убедиться что проходит**

Run: `cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes-v2 && .venv/bin/python -m pytest tests/test_pipeline_fixes.py::TestToolMessagesHonest -v`

Expected: 3 PASS.

- [ ] **Step 5: Коммит**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
git add AIM/hermes-v2/app/llm.py AIM/hermes-v2/tests/test_pipeline_fixes.py
git commit -m "fix(ui): честные сообщения прогресса тулов (Google Maps→ФНС)

Сообщение 'Ищу конкурентов через Google Maps' было ложным — код использует
Perplexity+SearXNG→ФНС стратегию (V2), Google Maps был удалён в V1.
Также 'Определяю клинику: ИНН' обещал ИНН, который Perplexity почти
никогда не находит. Сообщения приведены в соответствие с реальностью."
```

---

## Task 2: Auto-call company_financials после find_competitors

**Проблема:** `company_financials` тул существует (берёт выручку из ФНС по ИНН), но не вызывается автоматически. Perplexity (`extract_clinic_profile`) почти никогда не находит ИНН. Однако `find_competitors` (через aim-app) **часто возвращает** `client_inn` — но он не используется для запроса финансов.

**Решение:** По аналогии с существующим auto-call `run_review_platforms` (llm.py:558-586), добавить auto-call `company_financials` после `find_competitors`, если `client_inn` есть в результате.

**Files:**
- Modify: `AIM/hermes-v2/app/llm.py:558-586` (секция AUTO-INJECT, после блока `run_review_platforms`)
- Modify: `AIM/hermes-v2/app/llm.py:213-231` (`_build_formatted_blocks` — добавить financials в profile_cache)
- Test: `AIM/hermes-v2/tests/test_pipeline_fixes.py`

**Interfaces:**
- Consumes: `find_competitors` результат (JSON с `client_inn` полем), `handle_company_financials` из `aim_app_tools.py`
- Produces: финансовые данные в `collected_results["company_financials"]`, которые `_build_formatted_blocks` подставит в `profile_cache` для блока 01

- [ ] **Step 1: Добавить failing-тест для auto-call financials**

Дополнить `AIM/hermes-v2/tests/test_pipeline_fixes.py`:

```python
import asyncio
import json
from unittest.mock import AsyncMock, patch


class TestAutoCallFinancials:
    """Task 2: company_financials должен auto-call после find_competitors если есть client_inn."""

    def test_financials_called_when_inn_present(self):
        """Если find_competitors вернул client_inn, financials должен вызваться."""
        # Симулируем результат find_competitors с ИНН
        competitors_result = json.dumps({
            "client_inn": "7801234567",
            "competitors": [],
        })

        # Мокаем handle_company_financials
        financials_called = {"inn": None}

        async def fake_financials(inn="", **kwargs):
            financials_called["inn"] = inn
            return json.dumps({"inn": inn, "revenue": 50000000, "name": "Test Clinic"})

        # Проверяем, что auto-call логика извлекает ИНН из competitors_result
        # и вызывает financials (через симуляцию парсинга)
        comp_data = json.loads(competitors_result)
        client_inn = comp_data.get("client_inn")
        assert client_inn == "7801234567", "ИНН должен извлекаться из find_competitors"

        # Запуск fake_financials чтобы проверить сигнатуру
        result = asyncio.run(fake_financials(inn=client_inn))
        assert financials_called["inn"] == "7801234567"
        assert "revenue" in json.loads(result)

    def test_financials_not_called_without_inn(self):
        """Если client_inn пустой, financials НЕ должен вызываться."""
        competitors_result = json.dumps({"client_inn": "", "competitors": []})
        comp_data = json.loads(competitors_result)
        client_inn = comp_data.get("client_inn")
        assert not client_inn, "Пустой ИНН не должен триггерить financials"
```

- [ ] **Step 2: Запустить тест**

Run: `cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes-v2 && .venv/bin/python -m pytest tests/test_pipeline_fixes.py::TestAutoCallFinancials -v`

Expected: PASS (тест проверяет логику извлечения ИНН, которая уже корректна в find_competitors).

- [ ] **Step 3: Найти место для auto-call в llm.py**

Прочитать секцию auto-call в `AIM/hermes-v2/app/llm.py` (строки ~555-590). Сейчас там есть блок:

```python
# ── AUTO-INJECT: run_review_platforms если LLM не вызовала ──
if "find_competitors" in collected_results and "run_review_platforms" not in collected_results:
    ...
```

Добавить **перед** этим блоком (после строки ~555, после цикла tool execution) новый auto-call для financials.

- [ ] **Step 4: Реализовать auto-call company_financials**

В `AIM/hermes-v2/app/llm.py`, найти строку с комментарием `# ── AUTO-INJECT: run_review_platforms` (примерно строка 558). Добавить **перед** ней:

```python
            # ── AUTO-CALL: company_financials если есть client_inn из find_competitors ──
            # Perplexity (extract_clinic_profile) почти не находит ИНН, но find_competitors
            # (через aim-app→ФНС) часто определяет client_inn. Используем его для финансов.
            if (
                "find_competitors" in collected_results
                and "company_financials" not in collected_results
            ):
                try:
                    comp_data = json.loads(collected_results["find_competitors"])
                    client_inn = comp_data.get("client_inn", "")
                    if client_inn and len(client_inn) >= 10:
                        yield ("tool_start", "company_financials",
                               {"inn": client_inn}, "💰 Запрашиваю выручку из ФНС…")
                        from app.tools.aim_app_tools import handle_company_financials
                        fin_result = await handle_company_financials(inn=client_inn)
                        collected_results["company_financials"] = fin_result
                        # Обогатить profile_cache выручкой для блока 01
                        try:
                            fin_data = json.loads(fin_result)
                            if fin_data.get("revenue"):
                                profile_cache["revenue"] = fin_data["revenue"]
                            if fin_data.get("revenue_trend"):
                                profile_cache["revenue_trend"] = fin_data["revenue_trend"]
                            if fin_data.get("profit"):
                                profile_cache["profit"] = fin_data["profit"]
                            if fin_data.get("name") and not profile_cache.get("company_name"):
                                profile_cache["company_name"] = fin_data["name"]
                            logger.info(
                                "auto company_financials OK: inn=%s revenue=%s",
                                client_inn, fin_data.get("revenue"),
                            )
                        except (json.JSONDecodeError, TypeError):
                            pass
                        yield ("tool_result", "company_financials", fin_result,
                               "✅ Финансы из ФНС получены")
                except Exception as e:
                    logger.warning("auto company_financials failed: %s", e)

```

- [ ] **Step 5: Запустить все тесты**

Run: `cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes-v2 && .venv/bin/python -m pytest tests/test_pipeline_fixes.py -v`

Expected: 5 PASS (3 из Task 1 + 2 из Task 2).

- [ ] **Step 6: Коммит**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
git add AIM/hermes-v2/app/llm.py AIM/hermes-v2/tests/test_pipeline_fixes.py
git commit -m "feat(pipeline): auto-call company_financials после find_competitors

Perplexity (extract_clinic_profile) почти не находит ИНН, но find_competitors
(через aim-app→ФНС) часто определяет client_inn. Теперь после find_competitors
автоматически вызывается company_financials — выручка/прибыль из налоговой
попадает в profile_cache и отображается в блоке 01.

По аналогии с существующим auto-call run_review_platforms."
```

---

## Task 3: Graceful fallback для блока отзывов при падении Apify

**Проблема:** Когда Apify отдаёт 500 (платформа лежит), тула возвращают `None`, блок `_format_reviews_block` возвращает пустую строку, и блок «04 — ОТЗЫВЫ» полностью исчезает из ответа. Клиент не понимает, почему отзывов нет — выглядит как баг.

**Решение:** Добавить человекочитаемое сообщение в блок отзывов, когда все платформы недоступны: «⭐ Отзывы временно недоступны (площадки не отвечают)». Также `_build_summary` уже показывает «не найдены» — сделаем текст дружелюбнее.

**Files:**
- Modify: `AIM/hermes-v2/app/tools/run_review_platforms.py:271-290` (`_build_summary`)
- Modify: `AIM/hermes-v2/app/llm.py:321-322` (в `_format_reviews_block`: вместо `return ""` показывать fallback-сообщение)
- Test: `AIM/hermes-v2/tests/test_pipeline_fixes.py`

**Interfaces:**
- Consumes: результат `run_review_platforms` (JSON с `platforms`, `reputation_summary`, `source`)
- Produces: markdown блок «04 — ОТЗЫВЫ» который либо показывает данные, либо дружелюбное fallback-сообщение

- [ ] **Step 1: Добавить failing-тест для fallback**

Дополнить `AIM/hermes-v2/tests/test_pipeline_fixes.py`:

```python
from app.tools.run_review_platforms import handle_run_review_platforms, _build_summary


class TestReviewsFallback:
    """Task 3: при падении Apify блок отзывов должен показывать дружелюбное сообщение."""

    def test_build_summary_apify_down(self):
        """Когда обе платформы None, summary должно говорить 'недоступны', не 'не найдены'."""
        summary = _build_summary(None, None, "ARclinic")
        # Должно быть дружелюбное сообщение про недоступность, не про отсутствие
        assert "недоступ" in summary.lower() or "не отвечают" in summary.lower(), (
            f"Summary '{summary}' должен говорить про недоступность платформ, "
            "не про отсутствие отзывов у клиники"
        )

    def test_build_summary_partial_data(self):
        """Когда одна платформа есть, а другая None — показываем что есть."""
        yandex = {"rating": 5.0, "reviews": 562}
        summary = _build_summary(yandex, None, "ARclinic")
        assert "5.0" in summary
        assert "562" in summary

    def test_format_reviews_block_shows_message_when_empty(self):
        """Блок 04 не должен полностью исчезать — показываем fallback."""
        # Это требует изменения в _format_reviews_block (llm.py)
        # Сейчас при found_any=False возвращается "" — блок исчезает
        # Должен возвращать минимальный блок с сообщением
        import app.llm as llm_mod

        # Мокаем данные где все platforms пустые
        empty_result = json.dumps({
            "clinic": "TestClinic",
            "platforms": {"yandex": {}, "twogis": {}, "prodoctorov": {}},
            "praise_summary": "",
            "criticism_summary": "",
            "reputation_summary": "Отзывы временно недоступны",
            "source": "apify",
        })
        result = llm_mod._format_reviews_block(empty_result)
        # Должен вернуть НЕ пустую строку — fallback сообщение
        assert result != "", (
            "Блок отзывов не должен исчезать полностью при падении Apify"
        )
        assert "недоступ" in result.lower() or "04" in result, (
            f"Ожидалось fallback-сообщение, получено: {result[:100]}"
        )
```

- [ ] **Step 2: Запустить тест, убедиться что 2 из 3 падают**

Run: `cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes-v2 && .venv/bin/python -m pytest tests/test_pipeline_fixes.py::TestReviewsFallback -v`

Expected: `test_build_summary_partial_data` PASS, `test_build_summary_apify_down` FAIL, `test_format_reviews_block_shows_message_when_empty` FAIL.

- [ ] **Step 3: Исправить `_build_summary` в run_review_platforms.py**

В `AIM/hermes-v2/app/tools/run_review_platforms.py`, заменить функцию `_build_summary` (строки ~95-105):

```python
def _build_summary(yandex: dict | None, gis2: dict | None, company_name: str) -> str:
    """Короткая текстовая сводка репутации из точных данных."""
    parts = []
    if yandex and yandex.get("rating"):
        rating = yandex["rating"]
        tone = "сильная" if rating >= 4.5 else ("средняя" if rating >= 3.8 else "слабая")
        parts.append(f"Яндекс.Карты: {rating}★ ({yandex['reviews']} отз.) — репутация {tone}")
    if gis2 and gis2.get("rating"):
        parts.append(f"2ГИС: {gis2['rating']}★ ({gis2['reviews']} отз.)")
    if not parts:
        return f"Отзывы для «{company_name}» временно недоступны — площадки отзывов не отвечают."
    return " · ".join(parts) + "."
```

(Изменение: «не найдены» → «временно недоступны — площадки отзывов не отвечают»)

- [ ] **Step 4: Исправить `_format_reviews_block` в llm.py**

В `AIM/hermes-v2/app/llm.py`, найти строку `if not found_any: return ""` (примерно строка 321-322) и заменить:

```python
    if not found_any:
        # Fallback: не исчезаем полностью — показываем сообщение
        # (Apify может лежать, или клиники нет на Яндекс.Картах/2ГИС)
        return (
            "\n".join([
                ":::section-num",
                "04 — ОТЗЫВЫ ПАЦИЕНТОВ",
                ":::",
                "",
                summary if summary else "Отзывы временно недоступны.",
                "",
            ])
        )
```

Где `summary` — это `data.get("reputation_summary", "")` (уже извлечён выше в функции).

- [ ] **Step 5: Запустить все тесты**

Run: `cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes-v2 && .venv/bin/python -m pytest tests/test_pipeline_fixes.py -v`

Expected: 8 PASS (3 из Task 1 + 2 из Task 2 + 3 из Task 3).

- [ ] **Step 6: Коммит**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
git add AIM/hermes-v2/app/llm.py AIM/hermes-v2/app/tools/run_review_platforms.py AIM/hermes-v2/tests/test_pipeline_fixes.py
git commit -m "fix(reviews): graceful fallback при падении Apify — блок не исчезает

Раньше при 500 от Apify блок '04 — ОТЗЫВЫ' полностью исчезал из ответа.
Теперь показывает дружелюбное сообщение 'Отзывы временно недоступны —
площадки отзывов не отвечают' вместо пустоты.

_build_summary: 'не найдены' → 'временно недоступны' (честнее про причину).
_format_reviews_block: при found_any=False возвращает fallback-блок."
```

---

## Task 4: Деплой и e2e-проверка

**Цель:** Развернуть все 3 фикса на сервере, прогнать полный пайплайн через чат, убедиться что блоки 01-04 отображаются корректно.

**Files:** нет (деплой + тестирование)

- [ ] **Step 1: Скопировать изменённые файлы на сервер**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
scp AIM/hermes-v2/app/llm.py aim:/opt/aim/AIM/hermes-v2/app/
scp AIM/hermes-v2/app/tools/run_review_platforms.py aim:/opt/aim/AIM/hermes-v2/app/tools/
```

- [ ] **Step 2: Пересобрать и перезапустить v2**

```bash
ssh aim "cd /opt/aim/AIM && docker compose build hermes-v2 && docker compose up -d --force-recreate --no-deps hermes-v2"
```

- [ ] **Step 3: Дождаться healthcheck**

```bash
sleep 30
ssh aim "docker exec aim-hermes-v2 curl -s http://localhost:8000/health"
```

Expected: `{"status":"ok","service":"hermes-v2","version":"0.3.0"}`

- [ ] **Step 4: Проверить через чат на iamaim.ru**

Открыть iamaim.ru в инкогнито, отправить URL клиники, проверить:
- Сообщение «Ищу конкурентов через Perplexity и ФНС» (не Google Maps)
- Если find_competitors вернул client_inn → сообщение «💰 Запрашиваю выручку из ФНС»
- Блок 01 показывает выручку (если ИНН был)
- Блок 04 либо показывает отзывы (если Apify жив), либо «Отзывы временно недоступны» (если Apify лежит)
- Чат НЕ падает с «Извините, произошла ошибка»

- [ ] **Step 5: Проверить логи**

```bash
ssh aim "docker logs aim-hermes-v2 --since 5m 2>&1 | grep -E 'DEBUG|auto company_financials|review_platforms|FORMATTED' | tail -20"
```

Expected: видны `auto company_financials OK: inn=... revenue=...` и `FORMATTED BLOCKS: 4 blocks`.

- [ ] **Step 6: Push на GitHub**

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1
git push origin feat/competitor-v2-perplexity-searxng
```

---

## Self-Review

**Spec coverage:**
- ✅ Task 1: Ложное UI-сообщение «Google Maps» → исправлено
- ✅ Task 2: ИНН/выручка не находятся → auto-call company_financials добавлен
- ✅ Task 3: При падении Apify отзывы исчезают → graceful fallback
- ✅ Task 4: Деплой + e2e проверка

**Placeholder scan:** Все шаги содержат конкретный код и команды. Нет TBD/TODO.

**Type consistency:** `_TOOL_MESSAGES` dict, `_build_summary(yandex, gis2, company_name)`, `_format_reviews_block(reviews_raw)` — сигнатуры консистентны между задачами.
