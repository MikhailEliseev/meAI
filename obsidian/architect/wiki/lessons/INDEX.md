---
title: "Lessons Learned Index"
created: "2026-05-05"
updated: "2026-05-05"
total_lessons: 1
status: active
---

# Lessons Learned Index

Структурированное хранилище уроков из ошибок и успехов системы.

## Purpose

Lessons Learned система создана для:
1. **Предотвращения повторения ошибок** - агенты читают уроки перед задачами
2. **Обучения на опыте** - каждая проблема становится уроком
3. **Улучшения качества** - правила применяются автоматически
4. **Передачи знаний** - новые агенты учатся на опыте старых

## How to Use

### For Humans
1. Читай уроки перед похожими задачами
2. Добавляй новые уроки после багов/инцидентов
3. Обновляй статус уроков (active/resolved/obsolete)
4. Периодически review устаревших уроков

### For Agents
1. Перед execute_task() читай lessons по тегам задачи
2. Применяй Prevention Rules из уроков
3. Если встретил похожую проблему → проверь есть ли урок
4. После решения проблемы → создай новый урок

## Categories

- **bug** - баги и ошибки в коде
- **architecture** - архитектурные проблемы
- **performance** - проблемы производительности
- **ux** - проблемы пользовательского опыта
- **data-quality** - проблемы качества данных
- **validation** - проблемы валидации
- **integration** - проблемы интеграции

## Severity Levels

- **critical** - блокирует работу системы, требует немедленного исправления
- **high** - серьёзно влияет на качество, требует приоритетного исправления
- **medium** - заметно влияет на опыт, требует исправления
- **low** - минорное влияние, можно исправить позже

## All Lessons

### 2026-05-05

1. **[CI URL Validation Silent Failure](2026-05-05-ci-url-validation-silent-failure.md)**
   - Category: bug, data-quality, validation
   - Severity: critical
   - Status: active
   - Tags: `ci-system`, `validation`, `user-interaction`, `silent-failure`
   - Summary: CI Deep Analyzer вернул 0% без вопроса пользователю при неправильном URL

---

## Statistics

- **Total lessons:** 1
- **Active:** 1
- **Resolved:** 0
- **Obsolete:** 0

### By Category
- bug: 1
- data-quality: 1
- validation: 1

### By Severity
- critical: 1
- high: 0
- medium: 0
- low: 0

---

**Last Updated:** 2026-05-05
**Maintainer:** meAI Architect
