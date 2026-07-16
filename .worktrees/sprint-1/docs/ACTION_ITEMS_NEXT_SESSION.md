# Action Items для следующей сессии

**Дата создания:** 2026-05-11 00:27 GMT+3  
**Приоритет:** High  
**Контекст:** Budget Optimizer Agent (P1, Ads Magister)

## 🎯 Immediate Actions (сделать в начале сессии)

### 1. Использовать TaskCreate для отслеживания прогресса
```python
# В начале работы
TaskCreate(
    subject="Create Budget Optimizer Agent specification",
    description="Brief → Research → Write → Archive → Commit",
    activeForm="Creating Budget Optimizer specification"
)

# Создать подзадачи
TaskCreate(subject="Conduct user interview for Budget Optimizer", description="Interview user about budget optimization requirements")
TaskCreate(subject="Run deep research on budget optimization", description="Research budget allocation, bid optimization, ROI strategies")
TaskCreate(subject="Study existing budget optimization code", description="Check AIM/Old for existing implementations")
TaskCreate(subject="Write Budget Optimizer specification", description="Create full specification based on research and brief")
TaskCreate(subject="Archive research to vault", description="Run ingest_research.py")
TaskCreate(subject="Commit and push to GitHub", description="Create commit with specification")
```

### 2. Делать промежуточные коммиты
```bash
# После брифа
git add docs/briefs/BUDGET_OPTIMIZER_BRIEF.md
git commit -m "docs: add Budget Optimizer Agent brief"

# После research
git add obsidian/deep-research/
git commit -m "docs: archive Budget Optimizer research"

# После спецификации
git add docs/subagents-specs/BUDGET_OPTIMIZER_SPEC.md
git commit -m "docs: create Budget Optimizer Agent specification"

# Финальный push
git push origin main
```

### 3. Запускать research в фоне
```python
# Запустить research в фоне
Agent(
    description="Deep research on budget optimization",
    subagent_type="general-purpose",
    prompt="Budget optimization for medical marketing: allocation strategies, bid optimization, ROI, medical specifics",
    run_in_background=True
)

# Пока research идёт, изучить существующий код
Bash(command="find /Users/mikhaileliseev/Desktop/Dev/\!meAI/AIM/Old -type f -name '*budget*' -o -name '*optimizer*' | head -20")
```

### 4. Обновлять SESSION.md после каждого этапа
```python
# После каждого этапа
def update_session(stage: str, status: str, details: str):
    with open("SESSION.md", "a") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"### {status}: {stage}\n")
        f.write(f"{details}\n")
```

## 📋 Checklist перед началом работы

- [ ] Прочитать SESSION.md для восстановления контекста
- [ ] Прочитать MEMO-NEXT-SESSION.md для плана работы
- [ ] Создать задачи через TaskCreate
- [ ] Проверить наличие существующего кода в AIM/Old
- [ ] Запустить research в фоне (если нужно)

## 📋 Checklist перед коммитом

- [ ] Все задачи отмечены как completed
- [ ] SESSION.md обновлён
- [ ] MEMO-NEXT-SESSION.md обновлён
- [ ] Спецификация проверена (размер >30 KB, все секции заполнены)
- [ ] Research заархивирован в vault
- [ ] Git status чистый (нет uncommitted changes)

## 🚫 Что НЕ делать

1. ❌ Не вызывать Bash() без параметра command
2. ❌ Не создавать HTML файлы без запроса пользователя
3. ❌ Не пропускать интервью пользователя
4. ❌ Не делать один большой коммит в конце
5. ❌ Не забывать обновлять SESSION.md

## 📊 Метрики для отслеживания

**Target времени:**
- Бриф: 5-10 мин
- Deep research: 10-20 мин (запустить в фоне!)
- Анализ research: 5-10 мин
- Написание спецификации: 30-40 мин
- Архивирование: 5 мин
- Коммит: 5 мин
- **Итого:** 1-1.5 часа (не 3.5 часа как сегодня!)

**Target качества:**
- Размер спецификации: >30 KB
- Полнота секций: 100%
- Конкретность метрик: Да
- Использование существующего кода: Да

## 🎓 Применить lessons learned

1. **Mandatory interview** — начать с интервью
2. **Large file write** — использовать Write + Bash append
3. **Study existing code** — проверить AIM/Old перед написанием
4. **No HTML by default** — только Markdown
5. **Use TaskCreate** — создать задачи в начале
6. **Frequent commits** — коммитить после каждого этапа
7. **Parallel work** — research в фоне
8. **Session checkpoints** — обновлять SESSION.md

---

**Следующий агент:** Budget Optimizer Agent (P1, Ads Magister)  
**Estimated time:** 1-1.5 часа (с учётом улучшений)  
**Готовность:** ✅ Ready to start
