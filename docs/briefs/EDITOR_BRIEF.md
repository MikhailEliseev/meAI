# Бриф: Editor Agent

**Дата:** 2026-05-10  
**Приоритет:** P1  
**Родительский Magister:** Content Magister

## Назначение

Editor Agent — автоматизированный редактор контента для медицинского маркетинга. Проверяет и улучшает тексты, созданные Blog Content Agent и Landing Content Agent, обеспечивая высокое качество, медицинскую точность и соответствие бренд-гайдам.

**Основная задача:** Превратить черновик в публикационно-готовый текст через многоуровневую проверку (грамматика → стиль → ToV → факты → readability → polish).

## Контекст и специфика

**Медицинская специфика:**
- Обязательная проверка медицинских фактов (интеграция с Medical Fact-Checker Agent)
- Compliance: FDA guidelines, 152-ФЗ (РФ), E-E-A-T, YMYL
- Disclaimers и legal notices
- Точность терминологии

**Качество важнее скорости:**
- Глубокая проверка: 5-10 минут на статью 1,500 слов
- Все уровни проверки обязательны
- Никаких компромиссов ради скорости

**Tone of Voice:**
- Строгое соответствие бренд-гайдам
- Консистентность стиля во всех материалах
- Интеграция с Tone of Voice Agent

## Интеграции

**Входные данные:**
- `content_draft` (str) — черновик от Blog/Landing Content Agent
- `content_type` (str) — "blog" | "landing" | "email"
- `target_audience` (str) — целевая аудитория
- `brand_guidelines` (dict) — ToV правила
- `medical_context` (dict) — медицинский контекст для проверки фактов

**Выходные данные:**
- `edited_content` (str) — отредактированный текст
- `changes_summary` (dict) — что изменено и почему
- `quality_scores` (dict) — метрики качества
- `warnings` (list) — предупреждения (если есть)

**Связанные агенты:**
- **Blog Content Agent** — источник черновиков блогов
- **Landing Content Agent** — источник черновиков лендингов
- **Tone of Voice Agent** — проверка соответствия бренду
- **Medical Fact-Checker Agent** — проверка медицинских фактов
- **SEO Optimizer Agent** — SEO-оптимизация текста

**Внешние API:**
- **LanguageTool API** — грамматика, орфография, пунктуация
- **Grammarly API** (опционально) — расширенная проверка
- **Hemingway Editor API** — readability, упрощение
- **Claude API** — AI-powered suggestions
- **Textstat** (библиотека) — readability scores

## Приоритеты исследования

### 🔴 КРИТИЧНО (обязательно глубоко изучить)

1. **Грамматика и орфография**
   - LanguageTool API: возможности, лимиты, цены
   - Grammarly API: сравнение с LanguageTool
   - Поддержка русского и английского языков
   - Типичные ошибки в медицинском контенте

2. **Стиль и читаемость**
   - Hemingway Editor API: интеграция, метрики
   - Textstat: Flesch Reading Ease, Flesch-Kincaid Grade
   - Оптимальные значения readability для медицинского контента
   - Упрощение сложных предложений без потери точности

3. **Tone of Voice compliance**
   - Как проверять соответствие бренд-гайдам автоматически
   - Метрики консистентности стиля
   - Интеграция с Tone of Voice Agent
   - Примеры ToV правил для медицинского маркетинга

4. **Медицинская точность и compliance**
   - E-E-A-T критерии для медицинского контента
   - YMYL guidelines
   - FDA regulations для медицинского маркетинга
   - 152-ФЗ (РФ) требования
   - Disclaimers и legal notices
   - Интеграция с Medical Fact-Checker Agent

### 🟡 ВАЖНО (изучить, но не так глубоко)

1. **AI-powered suggestions**
   - Claude API для умных предложений по улучшению
   - Промпты для редактирования
   - Баланс между автоматикой и человеческим контролем

2. **SEO-оптимизация текста**
   - Плотность ключевых слов
   - Meta descriptions
   - Заголовки (H1-H6)
   - Интеграция с SEO Optimizer Agent

3. **Workflow и автоматизация**
   - Последовательность проверок (grammar → style → ToV → facts → readability → polish)
   - Batch processing для нескольких статей
   - Параллельные проверки vs последовательные
   - Retry логика для API

4. **Версионирование и track changes**
   - История изменений
   - Сравнение версий (diff)
   - Rollback к предыдущей версии
   - Формат хранения изменений

### 🟢 ОПЦИОНАЛЬНО (можно пропустить или поверхностно)

1. Интеграция с CMS (WordPress, Contentful)
2. Экспорт в разные форматы (Markdown, HTML, DOCX)
3. Collaborative editing (несколько редакторов)
4. Real-time editing (WebSocket)

## Метрики успеха

**Качество:**
- Grammar errors fixed: 100%
- Readability score: > 60 (Flesch Reading Ease)
- ToV compliance: > 90%
- Medical facts verified: 100%
- E-E-A-T compliance: 100%

**Производительность:**
- Time to edit: < 10 минут (для статьи 1,500 слов)
- API uptime: > 99%
- Error rate: < 1%

**Стоимость:**
- LanguageTool API: < $0.01 per check
- Claude API: < $0.05 per article
- Total cost per article: < $0.10

## Дополнительные материалы

**Интервью:** Нет (создано через бриф)  
**Связанные спецификации:**
- `BLOG_CONTENT_SPEC.md` — источник черновиков
- `LANDING_CONTENT_SPEC.md` — источник черновиков
- `TONE_OF_VOICE_SPEC.md` (TODO) — проверка ToV
- `MEDICAL_FACT_CHECKER_SPEC.md` (TODO) — проверка фактов

**TODO из других агентов:**
- Blog Content Agent: "Editor Agent должен проверять E-E-A-T compliance"
- Landing Content Agent: "Editor Agent должен проверять conversion-focused copy"

## Workflow (детальный)

```
1. Получить черновик от Blog/Landing Content Agent
2. Grammar check (LanguageTool API)
   ↓
3. Style check (Hemingway API + Textstat)
   ↓
4. ToV check (Tone of Voice Agent)
   ↓
5. Medical facts check (Medical Fact-Checker Agent)
   ↓
6. Readability optimization (Claude API suggestions)
   ↓
7. Final polish (Claude API)
   ↓
8. Generate changes summary + quality scores
   ↓
9. Return edited content + metadata
```

**Параллелизация:**
- Шаги 2-3 можно выполнять параллельно (независимые проверки)
- Шаги 4-5 можно выполнять параллельно (независимые проверки)
- Шаги 6-7 последовательно (зависят от предыдущих результатов)

## Примеры использования

**Пример 1: Редактирование блога**
```python
result = await editor_agent.execute({
    "content_draft": "Диабет это серьезное заболевание...",
    "content_type": "blog",
    "target_audience": "patients",
    "brand_guidelines": {...},
    "medical_context": {"topic": "diabetes", "audience": "patients"}
})

# result.edited_content: "Диабет — серьёзное заболевание..."
# result.changes_summary: {"grammar": 5, "style": 3, "tov": 2, "facts": 0}
# result.quality_scores: {"readability": 65, "tov_compliance": 95, "eeat": 100}
```

**Пример 2: Редактирование лендинга**
```python
result = await editor_agent.execute({
    "content_draft": "Запишитесь на прием сегодня!...",
    "content_type": "landing",
    "target_audience": "leads",
    "brand_guidelines": {...},
    "medical_context": {"service": "consultation", "specialty": "cardiology"}
})

# result.edited_content: "Запишитесь на приём сегодня!..."
# result.changes_summary: {"grammar": 2, "style": 5, "tov": 1, "facts": 0}
# result.quality_scores: {"readability": 70, "tov_compliance": 92, "eeat": 100}
```

---

**Автор:** Mikhail Eliseev (via meAI Architect)  
**Статус:** ✅ Готов для deep-research
