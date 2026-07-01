# 04 — ДИЗАЙН-СИСТЕМА AIM (КАНОН)

**Дата:** 1 июля 2026
**Статус:** Канон — единственный источник истины для дизайна
**Canonical reference:** `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html`

---

## ⚠️ ПРИНЦИПИАЛЬНО ВАЖНЫЕ ПРАВИЛА

1. **Двойная дизайн-система** — light и dark темы. Обе должны выглядеть идеально.
2. **Standalone HTML** для scout-постов — БЕЗ шапки сайта, БЕЗ header, БЕЗ footer.
3. **Шрифты:** Playfair Display (заголовки) + **Jost** (body). НЕ Inter. НЕ Montserrat. НЕ system.
4. **Переключатель темы** — круглый 28×28px, sun/moon SVG иконки, в правом верхнем углу.
5. **Анимации:** glass-glow, card-breathe, water ripple (только в light теме).
6. **Бейджи (metric tags):** 5 цветов с цветными dot индикаторами.
7. **localStorage ключ:** `aim-theme`
8. **Атрибут темы:** `data-theme="light"|"dark"` на `<html>`

---

## 🎨 ЦВЕТА (CSS переменные)

### Light theme (по умолчанию)

```css
:root {
  --bg: #ffffff;
  --surface: #fafafa;
  --hover: #f5f5f5;
  --border: #E0E0E0;
  --border-strong: #C0C0C0;
  --text: #1A1A1A;
  --text-secondary: #444444;
  --text-dim: #666666;
  --accent: #1A1A1A;        /* монументально-чёрный */
  --accent-hover: #333333;
  --card-bg: #ffffff;
  --card-hover: #fafafa;
  --glass-bg: rgba(255,255,255,0.85);
  --glass-border: rgba(0,0,0,0.08);
  --glow-outer: rgba(0,0,0,0.07);
  --glow-inner: rgba(0,0,0,0.025);
}
```

**Характер:** Монументально-чёрный на белом. Строгий, журнальный, премиум.

### Dark theme (Art Deco)

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
  --accent: #c9a96e;        /* Art Deco gold */
  --accent-hover: #e8cfa0;
  --card-bg: #1a1a1a;
  --card-hover: rgba(201,169,110,.05);
  --glass-bg: rgba(13,13,13,0.85);
  --glass-border: rgba(201,169,110,.10);
  --glow-outer: rgba(201,169,110,0.08);
  --glow-inner: rgba(201,169,110,0.03);
}
```

**Характер:** Art Deco gold на глубоком чёрном. Роскошный, кинематографичный.

---

## 📝 ТИПОГРАФИКА

### Шрифты Google Fonts

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Jost:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

### Применение

| Элемент | Семья | Вес | Размер | Letter-spacing | Line-height |
|---------|-------|-----|--------|----------------|-------------|
| **Логотип "AIM"** | Playfair Display | 400 | 1.875rem | -0.02em | 1 |
| **H1 hero** | Playfair Display | 400 | clamp(32px, 4vw, 48px) | -0.01em | 1.15 |
| **H2 секции** | Playfair Display | 400 | clamp(24px, 3vw, 36px) | -0.01em | 1.15 |
| **H3** | Playfair Display | 400 | 1.15rem | 0 | 1.3 |
| **H4** | Playfair Display | 400 | 1rem | 0 | 1.4 |
| **Body** | **Jost** | 400 | 16px | 0 | 1.7 |
| **Small** | Jost | 400 | 0.85rem | 0 | 1.5 |
| **Tag/Label** | Jost | 600 | 11px | 0.2em UPPER | 1 |
| **Buttons** | Jost | 600 | 13px | 0.1em UPPER | 1 |

### CSS

```css
h1, h2, h3, h4 {
  font-family: 'Playfair Display', Georgia, serif;
  font-weight: 400;
  line-height: 1.15;
  color: var(--text);
  letter-spacing: -.01em;
}

h1 { font-size: clamp(32px, 4vw, 48px); margin: 8px 0 4px; }
h2 { font-size: clamp(24px, 3vw, 36px); margin-bottom: 20px; color: var(--accent); }
h3 { font-size: 1.15rem; margin: 24px 0 12px; color: var(--text); }
h4 { font-size: 1rem; margin: 16px 0 8px; color: var(--text); }

body {
  font-family: 'Jost', -apple-system, sans-serif;
  font-weight: 400;
  font-size: 16px;
  line-height: 1.7;
}

.sec-tag {
  font-family: 'Jost', sans-serif;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: var(--accent);
}
```

---

## 🌊 АНИМАЦИИ

### Card-breathe (дышащие карточки)

```css
@keyframes card-breathe {
  0%, 100% { box-shadow: 0 2px 12px rgba(0,0,0,0.03); }
  50%      { box-shadow: 0 6px 24px rgba(0,0,0,0.07); }
}

.glass-card {
  animation: card-breathe 4s ease-in-out infinite;
}
```

### Glass-glow (свечение glass stats)

```css
@keyframes glass-glow {
  0%, 100% { box-shadow: 0 0 14px var(--glow-outer), inset 0 0 20px var(--glow-inner); }
  50%      { box-shadow: 0 0 22px var(--glow-outer), inset 0 0 30px var(--glow-inner); }
}

.glass-stat {
  animation: glass-glow 5s ease-in-out infinite;
}
```

### Water ripple rings (только в light теме)

```css
.ripple { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.ripple-ring { position: absolute; border-radius: 50%; border: 1px solid var(--text); opacity: 0.04; background: none; }

@keyframes pulse-ring {
  0%, 100% { opacity: 0.03; transform: scale(1); }
  50%      { opacity: 0.07; transform: scale(1.15); }
}

/* 8+ ripple rings разных размеров и позиций */
.ring-lg-1 { width: 420px; height: 420px; top: -12%; right: -8%; }
.ring-lg-2 { width: 340px; height: 340px; top: 15%; right: 70%; }
/* ... (полный набор в canonical reference) */

[data-theme="dark"] .ripple { display: none; }  /* В dark теме НЕ показываем */
```

### Background ambient glow

```css
body::before {
  content: '';
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(201,169,110,0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(201,169,110,0.02) 0%, transparent 40%),
    radial-gradient(ellipse at 50% 80%, rgba(201,169,110,0.03) 0%, transparent 50%);
}

[data-theme="light"] body::before {
  background:
    radial-gradient(ellipse at 20% 50%, rgba(0,0,0,0.02) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(0,0,0,0.015) 0%, transparent 40%);
}
```

---

## 🧩 КОМПОНЕНТЫ

### 1. Container (центрирующая обёртка)

```css
.container {
  max-width: 860px;
  margin: 0 auto;
  padding: 0 32px;
  position: relative;
  z-index: 1;
}
```

### 2. Section (секция отчёта)

```css
.section { padding: 60px 0 50px; }
.section:first-of-type { padding-top: 40px; }
```

### 3. Sec-tag (метка секции)

```html
<div class="sec-tag">Раздел 02 — Конкуренты</div>
```

```css
.sec-tag {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-family: 'Jost', sans-serif;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .2em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 20px;
}

.sec-tag::before {
  content: '';
  display: block;
  width: 32px;
  height: 1px;
  background: var(--accent);
}
```

### 4. Glass-card (основная карточка)

```html
<div class="glass-card">
  <h3>Заголовок</h3>
  <p>Содержимое...</p>
</div>
```

```css
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  padding: 28px 32px;
  margin: 20px 0;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  transition: transform .3s, box-shadow .3s;
  animation: card-breathe 4s ease-in-out infinite;
}

.glass-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}

[data-theme="light"] .glass-card:hover {
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}
```

### 5. Glass-stats-wrap (сетка метрик)

```html
<div class="glass-stats-wrap">
  <div class="glass-stat">
    <div class="glass-stat-value">4.5с</div>
    <div class="glass-stat-label">Время загрузки</div>
  </div>
  <div class="glass-stat">
    <div class="glass-stat-value">87</div>
    <div class="glass-stat-label">Отзывов на 2ГИС</div>
  </div>
</div>
```

```css
.glass-stats-wrap {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 16px;
  margin: 24px 0;
}

.glass-stat {
  background: var(--glass-bg);
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
  border: 1px solid var(--glass-border);
  border-radius: 6px;
  padding: 28px 20px;
  text-align: center;
  transition: transform .3s, border-color .3s;
  animation: glass-glow 5s ease-in-out infinite;
}

.glass-stat:hover {
  border-color: var(--accent);
  transform: translateY(-4px);
}

.glass-stat-value {
  font-family: 'Playfair Display', serif;
  font-size: clamp(28px, 3vw, 40px);
  font-weight: 400;
  color: var(--accent);
  line-height: 1;
  margin-bottom: 8px;
}

.glass-stat-label {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
```

### 6. Metric-tag / Badges (БЕЙДЖИ)

5 цветов для индикаторов. Каждый = цветной dot + текст.

```html
<span class="metric-tag metric-tag-green">Сильная сторона</span>
<span class="metric-tag metric-tag-red">Критическая проблема</span>
<span class="metric-tag metric-tag-yellow">Требует внимания</span>
<span class="metric-tag metric-tag-blue">Информация</span>
<span class="metric-tag metric-tag-gray">Нейтрально</span>
```

```css
.metric-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: .04em;
  text-transform: uppercase;
  border-radius: 1px;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.metric-tag::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.metric-tag-green  { color: #66bb6a; border-color: rgba(102,187,106,.3); }
.metric-tag-red    { color: #ef5350; border-color: rgba(239,83,80,.3); }
.metric-tag-yellow { color: #ffa726; border-color: rgba(255,167,38,.3); }
.metric-tag-blue   { color: #42a5f5; border-color: rgba(66,165,245,.3); }
.metric-tag-gray   { color: var(--text-dim); }
```

### 7. Surface-block (выделенный блок)

Два варианта: positive (green) и negative (red).

```html
<div class="surface-block surface-block-green">
  <p><strong>+15%</strong> конверсии при ускорении сайта на 2 секунды</p>
</div>

<div class="surface-block surface-block-red">
  <p>Сайт теряет <strong>30% посетителей</strong> до загрузки</p>
</div>
```

```css
.surface-block {
  background: var(--surface);
  border-left: 3px solid var(--accent);
  padding: 18px 24px;
  margin: 12px 0;
}

.surface-block p { font-weight: 500; color: var(--text); }

.surface-block-green { border-left-color: #66bb6a; }
.surface-block-red   { border-left-color: #ef5350; }
```

### 8. Glass-table-wrap (таблицы)

```html
<div class="glass-table-wrap">
  <table>
    <thead>
      <tr><th>Конкурент</th><th>Оборот</th><th>Врачи</th></tr>
    </thead>
    <tbody>
      <tr><td>Клиника A</td><td>120M₽</td><td>14</td></tr>
      <tr><td>Клиника B</td><td>85M₽</td><td>9</td></tr>
    </tbody>
  </table>
</div>
```

```css
.glass-table-wrap {
  background: var(--glass-bg);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  overflow: hidden;
  margin: 16px 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

thead { background: var(--surface); }

th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 11px;
  letter-spacing: .05em;
  text-transform: uppercase;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}

td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}

tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--surface); }

.trend-up     { color: #66bb6a; font-weight: 500; }
.trend-down   { color: #ef5350; font-weight: 500; }
.trend-stable { color: var(--text-dim); }
```

### 9. CTA Box (call to action в конце отчёта)

```html
<div class="cta-box">
  <h2>Хотите углубить разбор?</h2>
  <p>Это был поверхностный анализ. Если хотите увидеть детали по любой секции — у нас есть платная экспертиза.</p>
  <a href="mailto:hello@iamaim.ru" class="btn">Связаться</a>
</div>
```

```css
.cta-box {
  background: var(--glass-bg);
  backdrop-filter: blur(24px) saturate(1.5);
  -webkit-backdrop-filter: blur(24px) saturate(1.5);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: 48px 32px;
  text-align: center;
  margin: 24px 0;
  animation: card-breathe 4.5s ease-in-out infinite, glass-glow 5s ease-in-out infinite;
}

.cta-box h2 { margin-top: 0; }
.cta-box p { color: var(--text-secondary); max-width: 500px; margin: 0 auto 24px; }
```

### 10. Button

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 14px 36px;
  background: var(--accent);
  color: var(--bg);
  border: none;
  font-family: 'Jost', sans-serif;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: .1em;
  text-transform: uppercase;
  border-radius: 1px;            /* острые углы */
  cursor: pointer;
  transition: all .3s;
  text-decoration: none;
}

.btn:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
}
```

### 11. Theme toggle (переключатель)

```html
<button class="theme-toggle" id="themeToggle" aria-label="Сменить тему">
  <svg class="icon-sun" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="5"/>
    <line x1="12" y1="1" x2="12" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="23"/>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
    <line x1="1" y1="12" x2="3" y2="12"/>
    <line x1="21" y1="12" x2="23" y2="12"/>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
  </svg>
  <svg class="icon-moon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
</button>
```

```css
.theme-toggle {
  position: fixed;
  top: 24px;
  right: 24px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text);
  transition: all .2s;
  z-index: 100;
}

.theme-toggle:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* Sun видна в dark теме (для переключения на light) */
.icon-sun { display: none; }
.icon-moon { display: block; }
[data-theme="dark"] .icon-sun { display: block; }
[data-theme="dark"] .icon-moon { display: none; }
```

### 12. JavaScript для theme toggle

```html
<script>
const STORAGE_KEY = 'aim-theme';

function getTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  return 'dark';  /* по умолчанию dark */
}

function setTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem(STORAGE_KEY, t);
}

/* Применить тему до рендера (чтобы не было мигания) */
setTheme(getTheme());

/* Слушатель кнопки */
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      setTheme(current === 'dark' ? 'light' : 'dark');
    });
  }
});
</script>
```

**КРИТИЧНО:** `setTheme(getTheme())` должен выполняться ДО `DOMContentLoaded`, в `<head>`, чтобы не было FOUC (flash of unstyled content).

---

## 📄 СТРУКТУРА СТАНДАРТНОГО SCOUT-ПОСТА

```html
<!DOCTYPE html>
<html lang="ru" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>{Title} — AIM Research</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Jost:wght@300;400;500;600;700&display=swap" rel="stylesheet">

  <style>
    /* ВСЕ CSS переменные и компоненты из этого документа */
  </style>

  <script>
    /* Theme toggle скрипт — ДОМ рендер */
    setTheme(getTheme());
  </script>
</head>
<body>
  <!-- Water ripple (только light тема) -->
  <div class="ripple">
    <div class="ripple-ring ring-lg-1"></div>
    <div class="ripple-ring ring-lg-2"></div>
    <!-- ... 8+ rings -->
  </div>

  <!-- Theme toggle -->
  <button class="theme-toggle" id="themeToggle">...</button>

  <!-- Container с контентом -->
  <div class="container">

    <!-- Hero секция -->
    <section class="section">
      <div class="sec-tag">Разбор клиники</div>
      <h1>{Название клиники}</h1>
      <p class="text-meta">Анализ от {дата} · Город {город}</p>
    </section>

    <!-- Ключевые метрики -->
    <section class="section">
      <div class="sec-tag">Ключевые метрики</div>
      <div class="glass-stats-wrap">
        <div class="glass-stat">
          <div class="glass-stat-value">4.5с</div>
          <div class="glass-stat-label">Время загрузки</div>
        </div>
        <!-- 4-6 метрик -->
      </div>
    </section>

    <!-- Конкуренты (с бейджами) -->
    <section class="section">
      <div class="sec-tag">Конкуренты</div>
      <h2>5 клиник в радиусе 2 км</h2>

      <div class="glass-card">
        <h3>Клиника A</h3>
        <p><span class="metric-tag metric-tag-green">Сильный</span> 4.8 рейтинг</p>
        <p>Оборот: 120M₽ · 14 врачей · 3 филиала</p>
      </div>

      <div class="glass-card">
        <h3>Клиника B</h3>
        <p><span class="metric-tag metric-tag-red">Слабый</span> 3.9 рейтинг</p>
      </div>
    </section>

    <!-- Сильные стороны (surface-block-green) -->
    <section class="section">
      <div class="sec-tag">Сильные стороны</div>
      <div class="surface-block surface-block-green">
        <p>Высокий рейтинг на 2ГИС — 4.8 при 87 отзывах</p>
      </div>
      <div class="surface-block surface-block-green">
        <p>Активные соцсети: 12 постов за месяц</p>
      </div>
    </section>

    <!-- Слабые места (surface-block-red) -->
    <section class="section">
      <div class="sec-tag">Точки роста</div>
      <div class="surface-block surface-block-red">
        <p>Сайт грузится 4.5с — теряете ~30% посетителей</p>
      </div>
      <div class="surface-block surface-block-red">
        <p>Нет упоминаний в СМИ за последний год</p>
      </div>
    </section>

    <!-- Таблица сравнения -->
    <section class="section">
      <div class="sec-tag">Сравнение с конкурентами</div>
      <div class="glass-table-wrap">
        <table>
          <thead>
            <tr><th>Метрика</th><th>Вы</th><th>Лидер</th><th>Среднее</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>Время загрузки</td>
              <td><span class="trend-down">4.5с</span></td>
              <td><span class="trend-up">1.2с</span></td>
              <td><span class="trend-stable">2.8с</span></td>
            </tr>
            <!-- ... -->
          </tbody>
        </table>
      </div>
    </section>

    <!-- CTA -->
    <section class="section">
      <div class="cta-box">
        <h2>Хотите углубить разбор?</h2>
        <p>Это был поверхностный анализ. Если хотите увидеть детали по любой секции — у нас есть платная экспертиза.</p>
        <a href="mailto:hello@iamaim.ru" class="btn">Связаться</a>
      </div>
    </section>

  </div>

  <script>
    /* Theme toggle listener (после DOMContentLoaded) */
    document.addEventListener('DOMContentLoaded', () => {
      const btn = document.getElementById('themeToggle');
      if (btn) {
        btn.addEventListener('click', () => {
          const current = document.documentElement.getAttribute('data-theme');
          setTheme(current === 'dark' ? 'light' : 'dark');
        });
      }
    });
  </script>
</body>
</html>
```

---

## 📱 RESPONSIVE

### Mobile (768px и меньше)

```css
@media (max-width: 768px) {
  .container { padding: 0 20px; }
  .section { padding: 50px 0 40px; }
  .glass-card { padding: 20px 18px; }
  .glass-stats-wrap { grid-template-columns: repeat(2, 1fr); }
  .cta-box { padding: 32px 20px; }
  h1 { font-size: 1.75rem; }
  h2 { font-size: 1.3rem; }
  table { font-size: 0.8rem; }
  th, td { padding: 8px 10px; }
}

@media (max-width: 480px) {
  .glass-stats-wrap { grid-template-columns: 1fr; }
}
```

### Print

```css
@media print {
  body { background: #fff; color: #000; }
  body::before, .cta-box, .ripple, .theme-toggle { display: none; }
  .glass-card { box-shadow: none; border: 1px solid #ccc; backdrop-filter: none; }
}
```

---

## ✅ ЧЕК-ЛИСТ КАЧЕСТВА ОТЧЁТА

Перед публикацией каждого scout-поста:

- [ ] HTML начинается с `<!DOCTYPE html>` и заканчивается `</html>`
- [ ] `<html>` имеет `data-theme="dark"` (default)
- [ ] `<meta name="robots" content="noindex, nofollow">` присутствует
- [ ] Google Fonts подключены (Playfair Display + Jost)
- [ ] CSS переменные для обеих тем определены
- [ ] Theme toggle кнопка в правом верхнем углу
- [ ] Theme toggle JS работает (console: `localStorage.getItem('aim-theme')`)
- [ ] Water ripple rings отображаются в light теме
- [ ] Water ripple rings скрыты в dark теме
- [ ] Все glass-card имеют backdrop-filter
- [ ] Все glass-stat имеют анимацию glass-glow
- [ ] Бейджи (metric-tag) используются для индикаторов
- [ ] Surface-block-green для сильных сторон
- [ ] Surface-block-red для слабых мест
- [ ] Glass-table-wrap оборачивает все таблицы
- [ ] CTA-box в конце отчёта
- [ ] Responsive: проверено на 768px и 480px
- [ ] Print: не ломается при печати

---

*Этот документ — канон. Любые компоненты не из этого документа = баг. Любые шрифты кроме Playfair Display + Jost = баг. Любые цвета кроме указанных = баг.*
