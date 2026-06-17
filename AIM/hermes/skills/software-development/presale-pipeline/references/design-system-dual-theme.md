# AIM Dual-Theme Design System

**Дата:** 2026-06-12  
**Статус:** КАНОНИЧНАЯ — единственная дизайн-система AIM  
**Источник:** `design-showcase-dual-theme.html` (104 KB)  
**URL:** https://iamaim.ru/wp-content/themes/aim-theme/design-showcase-dual-theme.html

---

## Концепция

**Две темы, одна система:**

1. **Light (по умолчанию)** — Monochrome Black/White
   - Чистый, строгий, профессиональный
   - Акцент: чёрный (`#1A1A1A`)
   - Границы: серые (`#E0E0E0`, `#CFCFCF`)

2. **Dark (переключатель)** — Art Deco Gold/Black
   - Премиум, золото на тёмном
   - Акцент: золото (`#c9a96e`)
   - Границы: золотые полупрозрачные (`rgba(201,169,110,.18)`)

**Переключение:** кнопка в header, localStorage (`aim-theme`), автоопределение системной темы.

---

## CSS Custom Properties

### Light Theme (`:root`)
```css
:root {
    --bg: #ffffff;
    --surface: #F5F5F5;
    --hover: #EBEBEB;
    --border: #E0E0E0;
    --border-strong: #CFCFCF;
    --text: #1A1A1A;
    --text-secondary: #666666;
    --text-dim: #999999;
    --accent: #1A1A1A;
    --accent-hover: #333333;
    --card-bg: #F5F5F5;
    --card-hover: #EBEBEB;
    --glass-bg: rgba(255,255,255,0.85);
    --glass-border: rgba(0,0,0,0.06);
}
```

### Dark Theme (`[data-theme="dark"]`)
```css
[data-theme="dark"] {
    --bg: #0d0d0d;
    --surface: #1a1a1a;
    --hover: #262626;
    --border: rgba(201,169,110,.18);
    --border-strong: rgba(201,169,110,.35);
    --text: #f5f0e8;
    --text-secondary: #9e9489;
    --text-dim: #7a7268;
    --accent: #c9a96e;
    --accent-hover: #e8cfa0;
    --card-bg: #1a1a1a;
    --card-hover: rgba(201,169,110,.05);
    --glass-bg: rgba(13,13,13,0.85);
    --glass-border: rgba(201,169,110,.10);
}
```

---

## Типографика

- **Заголовки:** Playfair Display (serif)
- **Тело:** Inter (sans-serif)
- **Дополнительный:** Jost (sans-serif, для UI элементов)

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Jost:wght@300;400;500;600;700&display=swap');
```

---

## Компоненты

### Кнопки
- **Primary:** `background: var(--accent); color: var(--bg);`
- **Hover:** `background: var(--accent-hover)`
- **Outline:** `border: 1px solid var(--accent); background: transparent;`

### Карточки
- **Card:** `background: var(--card-bg); border: 1px solid var(--border);`
- **Glass:** `background: var(--glass-bg); backdrop-filter: blur(20px); border: 1px solid var(--glass-border);`

### Метрики (теги)
- **Зелёный (хорошо):** `background: rgba(46,125,50,0.1); color: var(--green-text);`
- **Жёлтый (внимание):** `background: rgba(245,124,0,0.1); color: #F57C00;`
- **Красный (проблема):** `background: rgba(211,47,47,0.1); color: #D32F2F;`

### Таблицы
- Простые, ч/б, zebra-строки
- Bold для выделения лучших показателей
- Без цветового кодирования в КП

### Разделители
- **Стандартный:** `1px solid var(--border)`
- **Золотой (dark only):** `linear-gradient(90deg, transparent 0%, var(--accent) 50%, transparent 100%)`

---

## Анимации

- **Water ripples:** 6 источников × 3 кольца, 9-12s, монохромные
- **Shimmer (активная задача):** moving gradient 2s
- **Pulse (индикатор работы):** dot-pulse 0.8s
- **Unlock glow:** зелёная вспышка при разблокировке задачи
- **ВСЕ анимации:** `@media (prefers-reduced-motion: reduce) { animation: none; }`

---

## Тема-переключатель

```html
<button class="theme-toggle" onclick="
    var h = document.documentElement;
    var next = h.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    h.setAttribute('data-theme', next);
    localStorage.setItem('aim-theme', next);
">
    <!-- SVG sun + moon icons -->
</button>
```

**Автоопределение (в `<head>`):**
```html
<script>
(function(){
    var t = localStorage.getItem('aim-theme');
    if (t === 'dark' || (t === null && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
})();
</script>
```

---

## Где применять

| Где | Файл | Статус |
|-----|------|--------|
| Сайт iamaim.ru | `theme.css` (WordPress) | ✅ Dual-theme |
| Лендинг (showcase) | `design-showcase-dual-theme.html` | ✅ Каноничный |
| Панель Гермеса | `hermes-task-panel.html` | ✅ Dual-theme |
| КП (коммерческие предложения) | `configurator_template.html` | ✅ Dual-theme |
| Шаблоны КП | `aim-offer-template.html` | ✅ Dual-theme |

---

## Запрещено

- ❌ Использовать хардкод-цвета (hex) — только `var(--xxx)`
- ❌ Использовать старые переменные (`--text-muted`, `--line`, `--line-strong`, `--surface-hover`, `--radius`, `--radius-lg`)
- ❌ Добавлять третью тему
- ❌ Менять названия CSS-переменных
- ❌ Использовать зелёный/красный/золотой текст в таблицах КП (правило из commercial-proposal-masterclass)

---

## Файлы (локально)

```
AIM/frontend/
├── design-showcase-dual-theme.html   # Каноничная дизайн-система (104 KB)
└── hermes-task-panel.html            # Панель оркестрации задач (54 KB)

AIM/theme/
└── theme.css                          # WordPress тема (dual-theme CSS vars + Tailwind utility mapping)
```

**На сервере:** только эти два HTML-файла. Все старые (artdeco-real, final, monochrome, original, v2, test) — удалены.
