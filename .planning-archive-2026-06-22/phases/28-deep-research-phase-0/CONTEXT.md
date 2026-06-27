# Phase 28: Deep Research Phase 0 — Mandatory Pre-Flight Intelligence

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** User requirements — пресейл должен начинаться с обязательного deep research клиники и ключевых врачей

<domain>
## Phase Boundary

**Проблема:** Сейчас пресейл-пайплайн стартует с технического аудита сайта (Phase 1), пропуская важнейший этап — глубокое изучение самой клиники и её врачей. Маркетинговый смысл КП теряется, когда мы не знаем, КТО именно работает в клинике. «Заслуженные» доктора (д.м.н., профессора, авторы методик) — это главный актив клиники, но система их не распознаёт.

**Цель:** Phase 0 — обязательный pre-flight deep research, который запускается ПЕРЕД основным пайплайном (технический аудит, соцсети, конкуренты). Результаты питают все последующие фазы.

**Что исследуем:**
1. **Клиника:** история, репутация, рейтинги (prodoctorov, docdoc, 2gis, yandex), юрлицо, лицензии, основатели, СМИ-упоминания
2. **Ключевые врачи:** стаж, образование, регалии (к.м.н., д.м.н., профессор, заслуженный врач РФ), публикации, соцсети, отзывы пациентов, членство в ассоциациях
3. **Авто-определение «звёзд»:** при обнаружении д.м.н., профессора, автора методик, заслуженного врача — автоматическое углублённое исследование

**Что НЕ исследуем (глубоко):**
- Конкуренты — только поверхностный анализ (название, сайт, специализация, примерная выручка)
- Честное указание в КП: «Это поверхностный анализ конкурентов. Детальный конкурентный анализ — после подписания договора.»
- Deep-анализ конкурентов — только постконтракт

**Граница:**
- Deep Research на клинику клиента + всех ключевых врачей = Phase 0 (обязательно)
- Поверхностный обход конкурентов = Phase 1 пресейла (как сейчас)
- Deep Research конкурентов = отдельная постконтрактная фаза (НЕ в этом спринте)
- Результаты Phase 0 → data.json → питают social-verifier, content-analyzer, html-kp-generator
</domain>

<decisions>
## Implementation Decisions

### D-01: Phase 0 — автономный, без confirmation gates
Следуя правилу «presale-no-interruption»: Phase 0 должен проходить полностью автономно. Никаких «нашёл доктора Круглика — исследовать?». Если врач обнаружен на сайте клиники → deep research автоматически.

### D-02: Приоритизация врачей
Не все врачи одинаково важны:
- **Tier 1 (звёзды):** д.м.н., профессора, заслуженные врачи РФ, авторы методик → углублённое исследование (СМИ, научные публикации, диссертации)
- **Tier 2 (ядро):** к.м.н., главные врачи, руководители отделений, стаж > 15 лет → полное исследование (соцсети, отзывы, регалии)
- **Tier 3 (команда):** остальные врачи → базовое исследование (ФИО, специализация, стаж, соцсети)

### D-03: Источники deep research
- prodoctorov.ru — рейтинги, отзывы, стаж
- docdoc.ru — отзывы, цены приёма
- 2gis.ru — рейтинг, отзывы
- yandex.ru/maps — рейтинг, отзывы
- eLibrary.ru — научные публикации врачей
- dissercat.com — диссертации
- СМИ-упоминания (web_search)
- Соцсети (Instagram, VK, Telegram) — через social-verifier
- nalog.ru / checko.ru / rusprofile — юрлицо, финансы, лицензии

### D-04: Формат выхода
Результаты сохраняются в `/root/work/presale/{client}/data.json` в секцию `deep_research`:
```json
{
  "deep_research": {
    "clinic": {
      "history": "...",
      "reputation": {...},
      "ratings": {...},
      "legal_entity": {...},
      "media_mentions": [...]
    },
    "doctors": [{
      "full_name": "...",
      "tier": "star|core|team",
      "experience_years": 24,
      "degrees": ["к.м.н."],
      "publications_count": 15,
      "patient_reviews_rating": 4.8,
      "social_profiles": {...},
      "auto_flagged_star": true
    }]
  }
}
```

### D-05: Интеграция с presale-pipeline
Phase 0 добавляется ПЕРЕД текущей Phase 1 (site audit + finance):
- Phase 0: Deep Research (эта фаза)
- Phase 1: Tech audit + Finance (существующая)
- Phase 2: Social verifier + Competitors
- Phase 3: Content analyzer
- Phase 4: HTML KP

Phase 0 findings → social-verifier получает готовые social-профили врачей (не ищет заново)
Phase 0 findings → content-analyzer получает регалии врачей для per-expert карточек
Phase 0 findings → html-kp-generator получает блок «О клинике» и «Ключевые врачи»
</decisions>

<canonical_refs>
### На сервере (ssh root@138.16.224.188)
- `/root/work/presale/` — рабочая директория пресейлов
- `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` — parent orchestrator
- `/root/.hermes/skills/software-development/social-verifier/SKILL.md` — 5-pass verifier (получает соцпрофили)
- `/root/.hermes/skills/software-development/financial-fetcher/SKILL.md` — финансы (юрлицо, лицензии)
- `/root/.hermes/skills/software-development/html-kp-generator/SKILL.md` — 12-block HTML

### Локально
- `.planning/ROADMAP.md` — Phase 28 добавлен
- Auto-memory: `feedback/presale-no-interruption.md` — правило нулевых прерываний

### Пример: VIP Clinic (vipclinic.vip)
- Deep Research выполнен 2026-06-06: Круглик С.В. (24 года, к.м.н., заслуженный), Круглик Е.В. (21 год, к.м.н., гл.врач), Попугаев П.В. (34 года, к.м.н.)
- Результаты в `/root/work/presale/vipclinic/data.json` (26KB)
- Auto-flagged stars: Круглик С.В. (24yr + к.м.н. + руководитель + СМИ)
</canonical_refs>

---
*Phase: 28-deep-research-phase-0*
*Context gathered: 2026-06-06 from user requirements + vipclinic deep research experience*
