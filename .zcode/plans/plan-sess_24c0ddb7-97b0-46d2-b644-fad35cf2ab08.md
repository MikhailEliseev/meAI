## План: новые CSS классы для верстки отчёта

### Механизм
В `parseMarkdown()` (inline-golden.php) добавить препроцессор: паттерн `:::class ... :::` → `<div class="class">...</div>`. DOMPurify уже разрешает `div` + `class`.

### Шаг 1: CSS классы (inline-golden.php)
Добавить стили для новых компонентов:

```css
/* Surface Block — акцентный блок с левой границей (не italic!) */
.message-bubble .surface-block {
    border-left: 3px solid var(--accent);
    background: var(--accent-soft);
    padding: 10px 14px;
    margin: 8px 0;
    border-radius: 0 6px 6px 0;
    font-style: normal;  /* НЕ italic */
}
.message-bubble .surface-block strong { color: var(--accent); }

/* Stat Card — крупная цифра */
.message-bubble .stat-card {
    display: inline-block;
    padding: 8px 14px;
    margin: 4px 6px 4px 0;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    font-style: normal;
}
.message-bubble .stat-card .stat-value {
    font-size: 1.4em;
    font-weight: 700;
    color: var(--accent);
    display: block;
}
.message-bubble .stat-card .stat-label {
    font-size: 0.85em;
    color: var(--text-secondary);
}

/* Section header — пронумерованная секция */
.message-bubble .section-num {
    font-size: 0.75em;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--accent);
    font-weight: 600;
}
```

### Шаг 2: Препроцессор в parseMarkdown()
```js
// :::class ... ::: → <div class="class">...</div>
const blockPattern = /:::(\w+)\s*\n([\s\S]*?)\n:::/g;
cleaned = cleaned.replace(blockPattern, (m, cls, content) => {
    return `<div class="${cls}">\n${content}\n</div>`;
});
```

### Шаг 3: Форматтеры используют ::: паттерны

**profile.py**:
```
:::section-num
01 — О КЛИНИКЕ
:::

### ООО «Огни Олимпа»

:::surface-block
📍 Москва, Чапаевский пер. 3
🔬 120 врачей
📅 С 2019 года · 6 лет на рынке
:::

:::stat-card
**1.9 млрд ₽**
выручка
:::
:::stat-card
**137 млн ₽**
прибыль 📈
:::
```

**competitors.py** — таблица остаётся, вывод в `:::surface-block`:
```
:::surface-block
**Главный вывод:** Ближайший конкурент...
:::
```

**llm.py _format_audit_block** — GEO в stat-card, проблемы в surface-block:
```
:::stat-card
**70/100**
GEO Score 🟢
:::

:::surface-block
✅ AI-краулеры открыты
❌ MedicalBusiness Schema отсутствует
⚠️ SEO: нет meta description
:::
```

### Шаг 4: blockquote CSS — убрать italic
Старый blockquote оставить (для настоящих цитат), но `font-style: normal` убрать не будем — просто не используем `>` в форматтерах.

### Файлы
1. `AIM/theme/chat-inline-golden.php` — CSS классы + препроцессор `:::`
2. `AIM/hermes-v2/app/formatters/profile.py` — `:::surface-block`, `:::stat-card`
3. `AIM/hermes-v2/app/formatters/competitors.py` — `:::surface-block` для вывода
4. `AIM/hermes-v2/app/llm.py` — `_format_audit_block`, `_format_reviews_block`