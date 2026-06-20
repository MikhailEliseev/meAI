#!/usr/bin/env python3
"""Phase 0 PERPLEXITY — iphk.ru.
Запускает perplexity_search (через DeepSeek) и сохраняет сырые данные в проект.
"""
import json, os, sys, time
from datetime import datetime
from openai import OpenAI

PROJECT = "/opt/hermes-data/projects/iphk.ru"
RAW = os.path.join(PROJECT, "raw-data")
os.makedirs(RAW, exist_ok=True)

# ── Config ──
LLM_URL = os.getenv("LLM_BASE_URL", os.getenv("OMNIROUTE_URL", "https://api.deepseek.com/v1"))
LLM_KEY = os.getenv("LLM_API_KEY") or os.getenv("OMNIROUTE_AUTH") or os.getenv("DEEPSEEK_API_KEY")
if not LLM_KEY:
    raise RuntimeError("No LLM API key in env")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

client = OpenAI(api_key=LLM_KEY, base_url=LLM_URL, timeout=120.0)

# ── Query (built like _build_perplexity_query for PERPLEXITY phase) ──
QUERY = """Мне нужна ключевая информация для конкурентного анализа. Клиника: «Институт пластической хирургии и косметологии (iphk.ru)», город Москва. Специализация: пластическая хирургия и косметология.

1. Найди ИНН, ОГРН, полное юридическое название, год основания, юридический адрес клиники «Институт пластической хирургии и косметологии (iphk.ru)» (источники: РБК Компании, rusprofile, zachestnyibiznes, list-org). Также найди лицензию, генерального директора, главного врача.

2. Дай данные по объёму рынка платных медицинских услуг в городе Москва за последние 2-3 года (в рублях, с темпами роста). Отдельно — по направлению «пластическая хирургия и косметология».

3. Найди 5-7 частных клиник-конкурентов клиники «Институт пластической хирургии и косметологии (iphk.ru)» в городе Москва. Ищи конкурентов С ТАКИМ ЖЕ ПРОФИЛЕМ: пластическая хирургия и косметология. Приоритет — клиники схожего или чуть большего масштаба по выручке. Если Москва — мегаполис (Москва, СПб), бери ближайший район/округ. Если город небольшой — бери весь город.
Для каждой ОБЯЗАТЕЛЬНО укажи: полное название, ТОЧНЫЙ URL (не «домен легко ищется», а конкретный https://...), физический адрес, чем отличается от клиники «Институт пластической хирургии и косметологии (iphk.ru)». Для каждого конкурента укажи рейтинг и количество отзывов на ПроДокторов, НаПоправку, Яндекс Карты (если есть). Не включай саму клинику «Институт пластической хирургии и косметологии (iphk.ru)» в список конкурентов. Источники: Яндекс Карты, 2ГИС, ПроДокторов, НаПоправку.

4. Опиши типичного пациента клиник направления «пластическая хирургия и косметология» в городе Москва: возраст, пол, доход, средний чек, как ищет клинику (поиск, карты, соцсети, сарафанное радио), критерии выбора.

5. Опиши тренды рынка частной медицины в городе Москва: цифровизация, телемедицина, превентивная медицина, укрупнение сетей. Регулирование: лицензирование, ФЗ-152, ФЗ-38 «О рекламе».

6. Найди слабые места конкурентов клиники «Институт пластической хирургии и косметологии (iphk.ru)», незанятые ниши и недоиспользованные маркетинговые каналы в городе Москва. На чём конкуренты теряют пациентов?

ВАЖНО: Где есть точные цифры — укажи с источником. Где точных цифр нет — дай обоснованную оценку. НЕ пиши «нет данных» если можно дать аргументированную оценку."""

SYSTEM_PROMPT = (
    "Ты — AI-аналитик медицинского маркетинга. "
    "Твоя задача — глубокий анализ и фактические ответы. "
    "Каждый факт подкрепляй источником. "
    "Без воды, без общих фраз. "
    "Если данных недостаточно — честно скажи об этом."
)

print(f"[{datetime.now().isoformat()}] Starting perplexity_search for iphk.ru...")
print(f"  Model: {LLM_MODEL} @ {LLM_URL}")

t0 = time.time()

try:
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": QUERY},
        ],
        temperature=0.3,
        max_tokens=12000,
    )
    raw_answer = resp.choices[0].message.content or ""
    elapsed = time.time() - t0
    usage = resp.usage.model_dump() if resp.usage else {}

    print(f"  Done in {elapsed:.0f}s. Tokens: {usage}")

    # Сохраняем сырой ответ
    raw_data = {
        "phase": "PERPLEXITY",
        "tool": "perplexity_search",
        "client": "Институт пластической хирургии и косметологии (iphk.ru)",
        "city": "Москва",
        "specialization": "пластическая хирургия и косметология",
        "timestamp": datetime.now().isoformat(),
        "source": f"llm ({LLM_MODEL})",
        "elapsed_seconds": round(elapsed, 1),
        "usage": usage,
        "question": QUERY,
        "raw_answer": raw_answer,
    }

    path = os.path.join(RAW, "phase-0-perplexity-raw.json")
    with open(path, "w") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"  Raw saved: {path} ({len(raw_answer)} chars)")

    # ── LLM Interpretation (структурирование) ──
    INTERPRET_PROMPT = f"""КЛИНИКА: Институт пластической хирургии и косметологии (iphk.ru). ГОРОД: Москва. СПЕЦИАЛИЗАЦИЯ: пластическая хирургия и косметология.

Ты работаешь с ГОТОВЫМ исследовательским отчётом Perplexity. Perplexity УЖЕ проверил источники. Твоя задача — СТРУКТУРИРОВАТЬ, а не перепроверять.

ПРАВИЛА:
1. ИЗВЛЕКАЙ всё, что есть в отчёте. Perplexity уже проверил достоверность.
2. Оценки (estimate) — легитимные данные. Извлекай их.
3. Если секция полностью отсутствует — «НЕТ ДАННЫХ».
4. Город всегда Москва. Другой город — игнорируй.
5. Только частные клиники (ООО, АО, ИП). Госучреждения — пропускай.
6. БУДЬ КРАТКИМ. Каждая секция — 1-5 строк. Никаких эссе и подробных описаний.

СТРУКТУРА ВЫВОДА (строго по порядку):

=== РЫНОК ===
- Объём рынка (рубли, год)
- 2-3 тренда
- Регулирование (лицензирование, ФЗ-152, ФЗ-38)

=== КЛИЕНТ ===
- ИНН: ...
- ОГРН: ...
- Полное название: ...
- Год основания: ...
- Лицензия: ...
- Руководитель: ...

=== ПАЦИЕНТЫ ===
- Портрет (возраст, пол, доход)
- Средний чек
- Как ищут клинику

=== ВОЗМОЖНОСТИ ===
- Слабые места конкурентов
- Незанятые ниши
- Недоиспользованные каналы

=== КОНКУРЕНТЫ ===
ТОЛЬКО клиники с подтверждённым URL. Для каждой — СТРОГО одна строка:
- Название: «...» | URL: https://... | Специализация: ... | Адрес: ...
Без URL — НЕ включай. Максимум 7 конкурентов. Если нет — «НЕТ ДАННЫХ».

ВОТ ОТЧЁТ PERPLEXITY:

{raw_answer}"""

    print(f"[{datetime.now().isoformat()}] Starting LLM interpretation...")
    t0 = time.time()

    resp2 = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "Ты — AI-аналитик агентства AIM. Твоя задача — структурировать исследовательские данные."},
            {"role": "user", "content": INTERPRET_PROMPT},
        ],
        temperature=0.3,
        max_tokens=4000,
    )
    interpretation = resp2.choices[0].message.content or ""
    usage2 = resp2.usage.model_dump() if resp2.usage else {}

    print(f"  Interpretation done in {time.time()-t0:.0f}s")

    # Сохраняем интерпретацию
    interpret_data = {
        "phase": "PERPLEXITY",
        "type": "interpretation",
        "timestamp": datetime.now().isoformat(),
        "usage": usage2,
        "interpretation": interpretation,
    }

    path2 = os.path.join(RAW, "phase-0-perplexity-interpretation.json")
    with open(path2, "w") as f:
        json.dump(interpret_data, f, ensure_ascii=False, indent=2)
    print(f"  Interpretation saved: {path2} ({len(interpretation)} chars)")

    # ── Print summary ──
    print("\n" + "="*80)
    print("RAW ANSWER (first 500 chars):")
    print("-"*80)
    print(raw_answer[:500])
    print("\n" + "="*80)
    print("INTERPRETATION:")
    print("-"*80)
    print(interpretation[:2000])

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
