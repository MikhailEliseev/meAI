---
kanban-plugin: board
---

## 🏗️ Архитектура

- [ ] **Архитектор** (Architect) #core #strategy
- [ ] **Система Принятия Решений** (Decision Maker) #core #learning
- [ ] **Оркестратор** (Orchestrator) #core #async
- [ ] **Система Отката** (Rollback System) #core #safety

## 🚧 В Разработке

- [ ] **Оператор** (Operator) #tactical #autonomous
- [ ] **Базовый Агент** (Base Agent) #agents #base
- [ ] **SEO Агент** (SEO Agent) #agents #seo
	- 📋 [[SEO Agent - ТЗ]]
	- 📍 `src/meai/agents/seo_agent.py`
	- **Статус:** ⏳ TODO
	- **Приоритет:** P1
	- **Дедлайн:** @{2026-05-10}
	- **Зависимости:**
		- ✅ Base Agent
		- ✅ Event Bus
		- ⏳ Obsidian Integration
	- **Ключевые функции:**
		- Анализ конкурентов
		- Подбор ключевых слов
		- Оптимизация контента
		- Мониторинг позиций
- [ ] **Контент Агент** (Content Agent) #agents #content
- [ ] **Рекламный Агент** (Ads Agent) #agents #ads

## 🧪 Тестирование

- [ ] **Шина Событий** (Event Bus) #infra #messaging
- [ ] **Хранилище Событий** (Event Store) #infra #persistence
- [ ] **Интеграция Obsidian** (Obsidian Integration) #infra #memory
- [ ] **База Данных** (Database) #infra #data
- [ ] **Фабрика Агентов** (Agent Factory) #infra #factory

## ✅ Развернуто

- [ ] **CLI Инструменты** (CLI Tools) #tools #cli
- [ ] **Тестовые Скрипты** (Test Scripts) #tools #testing

## 📋 Бэклог

- [ ] **SEO Магистр** (SEO Magister) #aim #magisters
- [ ] **Контент Магистр** (Content Magister) #aim #magisters
- [ ] **Рекламный Магистр** (Ads Magister) #aim #magisters
- [ ] **FastAPI Сервер** (FastAPI Server) #infra #api
- [ ] **Docker Настройка** (Docker Setup) #infra #docker
- [ ] **Мониторинг** (Monitoring) #infra #monitoring

%% kanban:settings
```
{"kanban-plugin":"board","show-checkboxes":true,"new-line-trigger":"shift-enter","date-trigger":"@","time-trigger":"@@","lane-width":350}
```
%%
