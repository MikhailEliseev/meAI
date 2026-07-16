# KP Mini-Site Design System

## Register

brand

## Brand Context

Мини-сайт коммерческого предложения Центра семейной психологии Выставкиной Т.А. Одностраничный лендинг с насыщенной визуальной подачей: градиенты, анимации, параллакс-эффекты. Цель — произвести впечатление экспертной глубины и технологической современности, не скатываясь в инфоцыганскую эстетику.

### Anti-references (for this surface)
- ❌ Purple-to-blue AI-slope gradients (Midjourney/DALL-E aesthetic)
- ❌ Rainbow spectrums, neon glow, glassmorphism ради glassmorphism
- ❌ Cookie-cutter startup templates (тостеры, вава-эффекты, confetti)
- ❌ Red timers, urgency popups, «ТОЛЬКО СЕГОДНЯ»

---

## Color Palette

### Primary Brand Colors

| Token | Hex | OKLCH | Usage |
|-------|-----|-------|-------|
| `--color-primary` | `#1A5C3E` | oklch(40% 0.10 165) | Deep green — основной акцент, CTA, заголовки |
| `--color-primary-light` | `#2E8B5E` | oklch(52% 0.12 165) | Hover, lighter accents |
| `--color-accent` | `#B8860B` | oklch(65% 0.11 85) | Dark gold — бейджи, акцентные элементы, рейтинг |
| `--color-accent-light` | `#D4A832` | oklch(72% 0.11 85) | Gold hover, decorative elements |

### Gradient Stops (KP-specific)

| Token | Value | Usage |
|-------|-------|-------|
| `--gradient-primary` | `linear-gradient(135deg, #1A5C3E 0%, #2E8B5E 50%, #1A7A4A 100%)` | Hero background overlay, primary CTA buttons |
| `--gradient-accent` | `linear-gradient(135deg, #B8860B 0%, #D4A832 50%, #C9A24D 100%)` | Achievement badges, accent cards |
| `--gradient-hero-bg` | `linear-gradient(180deg, #0F1A13 0%, #1C2833 40%, #F6F4F0 100%)` | Hero section full background |
| `--gradient-card` | `linear-gradient(135deg, rgba(26,92,62,0.08) 0%, rgba(184,134,11,0.08) 100%)` | Card subtle overlay |
| `--gradient-section` | `linear-gradient(180deg, #F6F4F0 0%, #EDE8E1 50%, #F6F4F0 100%)` | Section backgrounds |
| `--gradient-cta-glow` | `radial-gradient(ellipse at center, rgba(46,139,94,0.3) 0%, transparent 70%)` | CTA button glow behind |

### Neutrals

| Token | Hex | OKLCH | Usage |
|-------|-----|-------|-------|
| `--color-ink` | `#14181C` | oklch(15% 0.01 250) | Основной текст |
| `--color-ink-secondary` | `#4A5058` | oklch(38% 0.01 250) | Вторичный текст, цены |
| `--color-ink-muted` | `#7A828C` | oklch(52% 0.01 250) | Placeholder, consent |
| `--color-surface` | `#FFFFFF` | oklch(100% 0 0) | Фон карточек |
| `--color-bg` | `#F6F4F0` | oklch(96% 0.003 90) | Фон секций — тёплый бежевый |
| `--color-bg-warm` | `#EDE8E1` | oklch(93% 0.005 90) | Тёплый акцентный фон |
| `--color-bg-dark` | `#0F1A13` | oklch(15% 0.03 165) | Тёмный фон hero/cta |
| `--color-bg-footer` | `#0A0F0C` | oklch(10% 0.02 165) | Футер |

### Semantic

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-success` | `#2E7D32` | Успех, Telegram-блок |
| `--color-rating` | `#3B82F6` | Бейдж рейтинга |
| `--color-online` | `#10B981` | Бейдж «Онлайн» / пульсирующий индикатор |

---

## Typography

### Font Stack

```css
--font-display: 'Formular', 'Futura PT', -apple-system, BlinkMacSystemFont, sans-serif;
--font-body: 'Formular', 'Futura PT', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

### Type Scale

| Level | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| Display | clamp(2.5rem, 5vw, 4.5rem) | 700 | 1.1 | -0.025em | Hero-заголовок |
| h1 | clamp(2rem, 4vw, 3rem) | 700 | 1.2 | -0.015em | Заголовок страницы |
| h2 | clamp(1.5rem, 3vw, 2.25rem) | 700 | 1.25 | normal | Заголовок секции |
| h3 | 1.25rem (20px) | 600 | 1.3 | normal | Имя специалиста |
| h4 | 1rem (16px) | 600 | 1.4 | normal | Специализация |
| body | 1rem (16px) | 400 | 1.6 | normal | Основной текст |
| body-sm | 0.875rem (14px) | 400 | 1.5 | normal | Описания, FAQ |
| caption | 0.75rem (12px) | 400 | 1.4 | normal | Мета-информация |
| eyebrow | 0.75rem (12px) | 600 | 1.3 | 0.12em | UPPERCASE label секций |

---

## Spacing Scale

```css
--space-3xs: 4px;
--space-2xs: 8px;
--space-xs:  12px;
--space-sm:  16px;
--space-md:  24px;
--space-lg:  32px;
--space-xl:  48px;
--space-2xl: 64px;
--space-3xl: 96px;
--space-4xl: 128px;
```

### Section Spacing

| Context | Value |
|---------|-------|
| Section padding vertical | `--space-3xl` (96px) |
| Hero padding vertical | `--space-4xl` (128px) |
| Container max-width | 1200px |
| Card gap (grid) | `--space-md` (24px) |
| Card padding | `--space-lg` (32px) |

---

## Border Radius

```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 16px;
--radius-xl: 24px;
--radius-full: 9999px;
```

---

## Shadows

```css
--shadow-card: 0 2px 10px rgba(0, 0, 0, 0.06);
--shadow-card-hover: 0 8px 30px rgba(0, 0, 0, 0.10);
--shadow-button-hover: 0 4px 20px rgba(26, 92, 62, 0.35);
--shadow-header: 0 1px 4px rgba(0, 0, 0, 0.05);
--shadow-glow-green: 0 0 40px rgba(26, 92, 62, 0.25);
--shadow-glow-gold: 0 0 30px rgba(184, 134, 11, 0.2);
```

---

## Motion Design

### Timing Tokens

```css
--duration-instant: 100ms;
--duration-fast: 200ms;
--duration-normal: 350ms;
--duration-slow: 500ms;
--duration-glacial: 800ms;
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
--ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
```

### Transition Map

| Element | Property | Duration | Easing |
|---------|----------|----------|--------|
| Buttons | background, transform, box-shadow | 200ms | ease-out |
| Cards hover | transform: translateY(-6px), box-shadow | 350ms | ease-spring |
| Mobile menu | transform (slide-left) | 350ms | ease-in-out |
| Modal/popup | opacity, transform (scale+fade) | 350ms | ease-in-out |
| FAQ accordion | max-height, opacity | 400ms | ease-smooth |
| Filter tabs | color, background | 200ms | ease-out |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Gradients System

### Правила использования градиентов
- Градиенты всегда purpose-driven: либо создают глубину (hero), либо привлекают внимание к CTA, либо разделяют секции
- Никаких purple-to-blue, rainbow-spectrum, neon-over-neon
- Тёмные градиенты строятся от глубокого зелёного (#0F1A13) к тёмно-синему (#1C2833)
- Светлые градиенты — от тёплого бежевого (#F6F4F0) к кремовому (#EDE8E1)
- Акцентные градиенты используют золотую гамму (#B8860B → #D4A832)

### Hero Gradient

```css
.hero {
  background: linear-gradient(180deg, #0F1A13 0%, #14261A 30%, #1C2833 65%, #F6F4F0 100%);
  position: relative;
  overflow: hidden;
}
```

Многослойный: тёмный глубокий зелёный → тёмный сине-серый → тёплый бежевый внизу. Создаёт ощущение глубины и перехода от «серьёзного» к «тёплому».

### CTA Button Gradient

```css
.btn-primary {
  background: linear-gradient(135deg, #1A5C3E 0%, #2E8B5E 100%);
  position: relative;
}
.btn-primary::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: inherit;
  background: radial-gradient(ellipse at center, rgba(46,139,94,0.3) 0%, transparent 70%);
  z-index: -1;
  opacity: 0;
  transition: opacity 300ms var(--ease-out);
}
.btn-primary:hover::after {
  opacity: 1;
}
```

Кнопка с градиентом и внешним свечением при hover. Glow появляется плавно, не пульсирует постоянно (не отвлекает).

### Section Divider Gradient

```css
.section-divider {
  height: 80px;
  background: linear-gradient(180deg, #F6F4F0 0%, #EDE8E1 50%, #F6F4F0 100%);
}
```

Мягкий переход между секциями вместо жёсткой границы.

### Card Accent Gradient

```css
.card-featured {
  background: linear-gradient(135deg, rgba(26,92,62,0.06) 0%, rgba(184,134,11,0.06) 100%);
}
```

Едва заметный тёпло-зелёный градиент на featured-карточках.

---

## Pulsing Elements

### Правила
- Пульсация используется ТОЛЬКО для индикации «живого» состояния: онлайн, активность, новый контент
- Не используется для CTA кнопок (слишком агрессивно — нарушает анти-референс «не кричать»)
- Частота: медленная, успокаивающая (2.5–3s цикл)
- Амплитуда: минимальная (opacity 0.6→1.0 или scale 1→1.03)

### Online Status Indicator

```css
@keyframes pulse-online {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}

.online-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-online);
  display: inline-block;
  animation: pulse-online 2.5s ease-in-out infinite;
}
```

Зелёная точка рядом с «Принимаем запись онлайн» — мягкое дыхание.

### Live Badge

```css
@keyframes pulse-live {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
}

.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  background: rgba(16, 185, 129, 0.12);
  color: var(--color-online);
  font-size: var(--text-caption);
  font-weight: 600;
  animation: pulse-live 3s ease-in-out infinite;
}
```

Бейдж «Принимаем заявки» с расширяющимся ring-эффектом.

### Scroll CTA Subtle Pulse

```css
@keyframes pulse-gentle {
  0%, 100% { box-shadow: 0 0 0 0 rgba(26, 92, 62, 0.3); }
  50% { box-shadow: 0 0 0 12px rgba(26, 92, 62, 0); }
}

.cta-pulse {
  animation: pulse-gentle 3s ease-in-out infinite;
}
```

Только для финальной CTA-секции внизу страницы. Мягкое ring-расширение, не кнопка сама.

---

## Animation System

### Scroll-Triggered Entrance Animations

Все entrance-анимации запускаются при попадании элемента во viewport (Intersection Observer). Каждый элемент получает задержку через CSS custom property `--entrance-delay` для staggered-эффекта.

```css
/* Base state — hidden */
.animate-in {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 600ms var(--ease-out), transform 600ms var(--ease-out);
  transition-delay: var(--entrance-delay, 0ms);
}

/* Revealed state — Intersection Observer добавляет класс */
.animate-in.is-visible {
  opacity: 1;
  transform: translateY(0);
}
```

### Entrance Variants

| Variant | Initial State | Duration | Usage |
|---------|---------------|----------|-------|
| `fade-up` | opacity:0, translateY(30px) | 600ms | Секции, карточки, параграфы |
| `fade-in` | opacity:0 | 800ms | Hero-заголовок, крупные блоки |
| `slide-right` | opacity:0, translateX(-40px) | 600ms | Изображения, иллюстрации слева |
| `slide-left` | opacity:0, translateX(40px) | 600ms | Текст справа от изображений |
| `scale-in` | opacity:0, scale(0.92) | 500ms | Модальные окна, featured-карточки |

### Stagger Delays

```css
.stagger-1 { --entrance-delay: 0ms; }
.stagger-2 { --entrance-delay: 100ms; }
.stagger-3 { --entrance-delay: 200ms; }
.stagger-4 { --entrance-delay: 300ms; }
.stagger-5 { --entrance-delay: 400ms; }
```

### Counter Animation (Stats)

```css
@keyframes count-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.counter {
  font-size: var(--text-display);
  font-weight: 700;
  color: var(--color-primary);
  animation: count-up 800ms var(--ease-out) forwards;
  animation-play-state: paused;
}
.counter.is-visible { animation-play-state: running; }
```

Числа анимируются через JS (countUp от 0 до target за 2s), контейнер — через CSS entrance.

### FAQ Accordion

```css
.faq-answer {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: max-height 400ms var(--ease-smooth), opacity 300ms var(--ease-out);
}
.faq-item.open .faq-answer {
  max-height: 500px;
  opacity: 1;
}
.faq-icon {
  transition: transform 300ms var(--ease-out);
}
.faq-item.open .faq-icon {
  transform: rotate(45deg);
}
```

### Hover Micro-interactions

```css
/* Card lift */
.card {
  transition: transform 350ms var(--ease-spring), box-shadow 350ms var(--ease-out);
}
.card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-card-hover);
}

/* Button press */
.btn {
  transition: transform 150ms var(--ease-out), box-shadow 200ms var(--ease-out);
}
.btn:active {
  transform: scale(0.97);
}

/* Link underline reveal */
.link-underline {
  position: relative;
  text-decoration: none;
}
.link-underline::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 1px;
  background: currentColor;
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 300ms var(--ease-out);
}
.link-underline:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}
```

### Stats Counter Reveal

```css
@keyframes reveal-number {
  0% { filter: blur(8px); opacity: 0; transform: translateY(20px) scale(0.9); }
  60% { filter: blur(0); opacity: 1; transform: translateY(-4px) scale(1.02); }
  100% { transform: translateY(0) scale(1); }
}

.stat-number {
  animation: reveal-number 1s var(--ease-spring) forwards;
  animation-play-state: paused;
}
.stat-number.is-visible { animation-play-state: running; }
```

---

## Parallax System

### Правила
- Параллакс = глубина, не трюк. Используется для создания ощущения пространства.
- Максимум 3 слоя (background, midground, foreground).
- Скорость движения: 0.2× — 0.5× от скорости скролла.
- На мобильных (<768px) параллакс отключается (transform: none).
- Не используется на critical content (текст, CTA). Только декоративные элементы.

### Hero Multi-Layer Parallax

```html
<div class="hero-parallax">
  <div class="parallax-layer layer-deep" data-speed="0.15">
    <!-- Крупные размытые круги/формы, самые дальние -->
  </div>
  <div class="parallax-layer layer-mid" data-speed="0.3">
    <!-- Средние полупрозрачные геометрические фигуры -->
  </div>
  <div class="parallax-layer layer-close" data-speed="0.5">
    <!-- Мелкие элементы ближе к зрителю -->
  </div>
  <div class="hero-content">
    <!-- Контент — статичен -->
  </div>
</div>
```

```css
.hero-parallax {
  position: relative;
  overflow: hidden;
  height: 100vh;
  min-height: 600px;
}

.parallax-layer {
  position: absolute;
  inset: -20%;
  will-change: transform;
}

.layer-deep {
  /* Медленное движение — дальний план */
  --parallax-speed: 0.15;
}

.layer-mid {
  --parallax-speed: 0.3;
}

.layer-close {
  --parallax-speed: 0.5;
}

@media (max-width: 768px) {
  .parallax-layer {
    transform: none !important;
  }
}
```

JS (requestAnimationFrame):
```javascript
const layers = document.querySelectorAll('.parallax-layer');
window.addEventListener('scroll', () => {
  requestAnimationFrame(() => {
    const scrollY = window.scrollY;
    layers.forEach(layer => {
      const speed = parseFloat(layer.dataset.speed);
      layer.style.transform = `translateY(${scrollY * speed}px)`;
    });
  });
});
```

### Water Ripple Background (Hero)

Эффект «круги на воде от брошенных камней» — замена floating blobs.
Концентрические кольца расходятся от нескольких точек падения, затухая по мере расширения.

**Принцип:**
- 3 точки падения (ripple origins) в разных местах hero-секции
- Из каждой точки расходятся 3 концентрических кольца (ripple rings)
- Кольца расширяются от `scale(0.1)` до `scale(1)`, opacity падает с 0.55 до 0
- Разная длительность (5s, 7s, 6s) и stagger-задержки (0s, 33%, 66%) — создают эффект случайных падений
- Цвета: `--color-primary` (зелёный), `--color-accent` (золотой), `--color-primary-light` (светло-зелёный)

```css
.hero-ripples { position: absolute; inset: 0; pointer-events: none; }

.ripple-origin {
  position: absolute;
  border-radius: 50%;
}

.ripple-origin--1 {
  width: 320px; height: 320px;
  top: 2%; left: 8%;
  color: var(--color-primary);
}
.ripple-origin--2 {
  width: 440px; height: 440px;
  bottom: 12%; right: -2%;
  color: var(--color-accent);
}
.ripple-origin--3 {
  width: 280px; height: 280px;
  top: 40%; left: 42%;
  color: var(--color-primary-light);
}

.ripple-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid;
  border-color: currentColor;
  opacity: 0;
  will-change: transform, opacity;
  animation: ripple-expand var(--ripple-duration, 5s) ease-out infinite;
}

.ripple-ring--1 { animation-delay: 0s; }
.ripple-ring--2 { animation-delay: calc(var(--ripple-duration, 5s) * 0.33); }
.ripple-ring--3 { animation-delay: calc(var(--ripple-duration, 5s) * 0.66); }

@keyframes ripple-expand {
  0%   { transform: scale(0.1); opacity: 0.55; border-width: 1.8px; }
  30%  { opacity: 0.35; }
  100% { transform: scale(1);   opacity: 0;    border-width: 0.2px; }
}
```

```html
<div class="hero-ripples" aria-hidden="true">
  <div class="ripple-origin ripple-origin--1" style="--ripple-duration: 5s">
    <div class="ripple-ring ripple-ring--1"></div>
    <div class="ripple-ring ripple-ring--2"></div>
    <div class="ripple-ring ripple-ring--3"></div>
  </div>
  <div class="ripple-origin ripple-origin--2" style="--ripple-duration: 7s">
    <div class="ripple-ring ripple-ring--1"></div>
    <div class="ripple-ring ripple-ring--2"></div>
    <div class="ripple-ring ripple-ring--3"></div>
  </div>
  <div class="ripple-origin ripple-origin--3" style="--ripple-duration: 6s">
    <div class="ripple-ring ripple-ring--1"></div>
    <div class="ripple-ring ripple-ring--2"></div>
    <div class="ripple-ring ripple-ring--3"></div>
  </div>
</div>
```

**Performance:** `will-change: transform, opacity` только на `.ripple-ring`. Все анимации composite-only.
**Reduced motion:** `.ripple-ring { animation: none !important; }`
**Цвета:** наследуются через `color` + `currentColor` на border — каждая точка падения задаёт свой цвет.

### Scroll-Progress Indicator

```css
.scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
  z-index: 9999;
  transform-origin: left;
  transition: transform 50ms linear;
}
```

### Section Transition Parallax

Секции с фоновым изображением/градиентом, двигающимся медленнее контента:

```css
.section-bg-parallax {
  background-attachment: fixed;
  background-position: center;
  background-size: cover;
}

@media (max-width: 768px) {
  .section-bg-parallax {
    background-attachment: scroll;
  }
}
```

---

## Component Library

### Buttons

| Variant | Background | Text | Radius | Usage |
|---------|-----------|------|--------|-------|
| Primary | `--gradient-primary` | white | `--radius-md` | «Записаться», основной CTA |
| Primary Glow | `--gradient-primary` + `::after` glow | white | `--radius-md` | Финальный CTA внизу |
| Accent | `--gradient-accent` | `--color-ink` | `--radius-md` | «Подобрать специалиста» (quiz) |
| Outline Dark | transparent + white border | white | `--radius-md` | Hero, тёмный фон |
| Secondary | transparent | `--color-primary` | `--radius-md` | «О специалисте» |

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 28px;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  min-height: 48px;
  min-width: 48px;
  transition: transform 150ms var(--ease-out),
              box-shadow 200ms var(--ease-out),
              background 200ms var(--ease-out);
}
.btn:active { transform: scale(0.97); }
.btn:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
```

### Cards (Specialist)

```
┌──────────────────────────────┐
│ [Photo]                      │
│                              │
│ [Badge: Кандидат наук]       │
│                              │
│ Name (h3, 20px, 600)         │
│ Title · N лет (body-sm)      │
│                              │
│ Description (body-sm, 2-line)│
│                              │
│ Цена · ₽ (body, muted)       │
│                              │
│ [Записаться] [О специалисте] │
└──────────────────────────────┘
```

```css
.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: var(--shadow-card);
  transition: transform 350ms var(--ease-spring),
              box-shadow 350ms var(--ease-out);
}
.card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-card-hover);
}
```

### Badges

| Variant | Background | Text | Animation |
|---------|-----------|------|-----------|
| Achievement | `--gradient-accent` | `--color-ink` | none |
| Online | `--color-online` | white | pulse-online (2.5s) |
| Rating | `--color-rating` | white | none |
| Live | transparent + ring | `--color-online` | pulse-live ring (3s) |

### Form Fields

```css
.input {
  background: var(--color-surface);
  border: 1px solid #D1D5DB;
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 1rem;
  transition: border-color 200ms var(--ease-out),
              box-shadow 200ms var(--ease-out);
}
.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(26, 92, 62, 0.12);
}
.input.error {
  border-color: #DC2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.08);
}
```

### Navigation

Desktop: горизонтальная, sticky, backdrop-blur при скролле.
Mobile: hamburger → slide-in меню слева.

```css
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: box-shadow 300ms var(--ease-out);
}
.header.scrolled {
  box-shadow: var(--shadow-header);
}
```

**Breakpoints:**
- Desktop: ≥1024px
- Tablet: 768px–1023px
- Mobile: <768px (single column, parallax disabled)

### Filter Tabs

Горизонтальный ряд кнопок-фильтров с активным состоянием.

```css
.filter-tab {
  padding: 10px 20px;
  border: 1px solid #D1D5DB;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-ink-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms var(--ease-out);
}
.filter-tab.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}
.filter-tab:hover:not(.active) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
```

### FAQ Accordion

```css
.faq-item {
  border-bottom: 1px solid #E5E7EB;
  padding: var(--space-md) 0;
}
.faq-question {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  background: none;
  border: none;
  padding: 0;
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}
.faq-answer {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: max-height 400ms var(--ease-smooth),
              opacity 300ms var(--ease-out);
  color: var(--color-ink-secondary);
  line-height: 1.6;
}
.faq-item.open .faq-answer {
  max-height: 500px;
  opacity: 1;
  padding-top: var(--space-sm);
}
```

### Floating Contact Bar

Фиксированный блок справа внизу. Иконки мессенджеров + телефон в кругах.

```css
.floating-contact {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 90;
}
.floating-contact .contact-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-card);
  transition: transform 200ms var(--ease-out);
}
.floating-contact .contact-btn:hover {
  transform: scale(1.1);
}
```

---

## Page Sections Map

### 1. Hero (100vh, water ripple + parallax 3-layer)
- Заголовок display + подзаголовок (fade-in entrance)
- Тёмный градиентный фон с эффектом «круги на воде» (water ripple) + parallax-слоями для глубины
- 3 точки падения камней: зелёный (top-left), золотой (bottom-right), светло-зелёный (center)
- Из каждой точки расходятся 3 концентрических кольца с разной задержкой (stagger 0s/33%/66%)
- CTA-кнопки: «Смотреть разбор» (primary) + «Конкуренты» (outline)
- Статистика: 32 / 21 / 174 / 8,5 млн (counter animation on scroll)

### 2. Trust Strip (padding: 24px 0)
- Логотипы/награды/сертификаты в ряд
- Entrance: fade-up staggered

### 3. Проблематика (bg: warm)
- Краткий блок «Когда стоит обратиться»
- 3-4 иконки с подписями в grid
- Entrance: fade-up staggered

### 4. Направления работы (bg: surface)
- 6 карточек-направлений в grid 3×2
- Каждая карточка: иконка, название, краткое описание
- Hover: translateY(-6px) + shadow
- Entrance: fade-up staggered по рядам

### 5. Специалисты (bg: warm)
- 3-4 карточки специалиста
- Фильтр-табы для выбора направления
- Entrance: scale-in staggered

### 6. Как мы работаем (bg: surface)
- 4-шаговый процесс в горизонтальный ряд
- Step numbers (counter animation)
- Соединительная линия между шагами
- Entrance: fade-up sequential

### 7. О центре + Преимущества (bg: gradient-section)
- Двухколоночный: текст слева, цифры/факты справа
- Entrance: slide-right (текст) + slide-left (цифры)

### 8. FAQ (bg: surface)
- 5-6 вопросов аккордеоном
- Entrance: fade-up

### 9. CTA Final (bg: dark gradient + parallax)
- Финальный призыв к действию
- Кнопка с glow-эффектом (pulse-gentle)
- Телефон, Telegram, WhatsApp
- Entrance: scale-in

### 10. Footer (bg: darkest)
- Логотип, контакты, карта проезда
- Ссылки, копирайт

---

## Implementation Notes

### Scroll Animation Trigger (Intersection Observer)

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      // Если счётчик — запустить count-up
      if (entry.target.classList.contains('counter')) {
        animateCounter(entry.target);
      }
    }
  });
}, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.animate-in, .counter, .stat-number')
  .forEach(el => observer.observe(el));
```

### Parallax RAF Throttle

```javascript
let ticking = false;
window.addEventListener('scroll', () => {
  if (!ticking) {
    requestAnimationFrame(() => {
      updateParallax();
      ticking = false;
    });
    ticking = true;
  }
});
```

### CSS Custom Properties for Parallax

```css
.parallax-layer {
  --parallax-y: 0;
  transform: translateY(var(--parallax-y));
}
```

JS обновляет `--parallax-y` через `element.style.setProperty('--parallax-y', ...)`.

### Performance Constraints
- Все анимации на `transform` и `opacity` (composite-only, без layout/paint trigger)
- `will-change` только на элементах с parallax (не на всех анимированных)
- Parallax отключён на mobile (<768px)
- `prefers-reduced-motion` уважается глобально
- Изображения: WebP с lazy loading
- Шрифты: `font-display: swap`

---

## CSS Custom Properties — Complete Set

```css
:root {
  /* Colors */
  --color-primary: #1A5C3E;
  --color-primary-light: #2E8B5E;
  --color-accent: #B8860B;
  --color-accent-light: #D4A832;
  --color-ink: #14181C;
  --color-ink-secondary: #4A5058;
  --color-ink-muted: #7A828C;
  --color-surface: #FFFFFF;
  --color-bg: #F6F4F0;
  --color-bg-warm: #EDE8E1;
  --color-bg-dark: #0F1A13;
  --color-bg-footer: #0A0F0C;
  --color-success: #2E7D32;
  --color-rating: #3B82F6;
  --color-online: #10B981;

  /* Gradients */
  --gradient-primary: linear-gradient(135deg, #1A5C3E 0%, #2E8B5E 50%, #1A7A4A 100%);
  --gradient-accent: linear-gradient(135deg, #B8860B 0%, #D4A832 50%, #C9A24D 100%);
  --gradient-hero: linear-gradient(180deg, #0F1A13 0%, #14261A 30%, #1C2833 65%, #F6F4F0 100%);
  --gradient-card: linear-gradient(135deg, rgba(26,92,62,0.06) 0%, rgba(184,134,11,0.06) 100%);
  --gradient-section: linear-gradient(180deg, #F6F4F0 0%, #EDE8E1 50%, #F6F4F0 100%);

  /* Typography */
  --font-display: 'Formular', 'Futura PT', -apple-system, sans-serif;
  --font-body: 'Formular', 'Futura PT', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --text-display: clamp(2.5rem, 5vw, 4.5rem);
  --text-h1: clamp(2rem, 4vw, 3rem);
  --text-h2: clamp(1.5rem, 3vw, 2.25rem);
  --text-h3: 1.25rem;
  --text-body: 1rem;
  --text-body-sm: 0.875rem;
  --text-caption: 0.75rem;
  --text-eyebrow: 0.75rem;
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
  --leading-display: 1.1;
  --leading-heading: 1.2;
  --leading-body: 1.6;
  --leading-caption: 1.4;
  --tracking-display: -0.025em;
  --tracking-eyebrow: 0.12em;

  /* Spacing */
  --space-3xs: 4px; --space-2xs: 8px; --space-xs: 12px;
  --space-sm: 16px; --space-md: 24px; --space-lg: 32px;
  --space-xl: 48px; --space-2xl: 64px; --space-3xl: 96px;
  --space-4xl: 128px;

  /* Radii */
  --radius-sm: 4px; --radius-md: 8px; --radius-lg: 16px;
  --radius-xl: 24px; --radius-full: 9999px;

  /* Shadows */
  --shadow-card: 0 2px 10px rgba(0,0,0,0.06);
  --shadow-card-hover: 0 8px 30px rgba(0,0,0,0.10);
  --shadow-button-hover: 0 4px 20px rgba(26,92,62,0.35);
  --shadow-glow-green: 0 0 40px rgba(26,92,62,0.25);
  --shadow-glow-gold: 0 0 30px rgba(184,134,11,0.2);

  /* Motion */
  --duration-instant: 100ms;
  --duration-fast: 200ms;
  --duration-normal: 350ms;
  --duration-slow: 500ms;
  --duration-glacial: 800ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## Keyframe Animations — Complete Set

```css
/* Pulse — online indicator */
@keyframes pulse-online {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
}

/* Pulse — live badge ring */
@keyframes pulse-live {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
}

/* Pulse — CTA glow (gentle, section-final only) */
@keyframes pulse-gentle {
  0%, 100% { box-shadow: 0 0 0 0 rgba(26, 92, 62, 0.3); }
  50% { box-shadow: 0 0 0 12px rgba(26, 92, 62, 0); }
}

/* Stats counter reveal */
@keyframes reveal-number {
  0% { filter: blur(8px); opacity: 0; transform: translateY(20px) scale(0.9); }
  60% { filter: blur(0); opacity: 1; transform: translateY(-4px) scale(1.02); }
  100% { transform: translateY(0) scale(1); }
}

/* Water ripple — hero background rings */
@keyframes ripple-expand {
  0%   { transform: scale(0.1); opacity: 0.55; border-width: 1.8px; }
  30%  { opacity: 0.35; }
  100% { transform: scale(1);   opacity: 0;    border-width: 0.2px; }
}

/* Skeleton loading */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```
