# Design

## Color Palette

### Primary Brand Colors

| Token | Hex | OKLCH | Usage |
|-------|-----|-------|-------|
| `--color-primary` | `#2E7D5F` | oklch(52% 0.12 170) | Primary green — CTA кнопки, акценты |
| `--color-primary-hover` | `#23684D` | oklch(44% 0.12 170) | Hover state primary |
| `--color-accent` | `#C9A24D` | oklch(72% 0.11 85) | Gold/amber — бейджи, акцентные элементы, рейтинг |
| `--color-accent-hover` | `#B8933E` | oklch(65% 0.11 85) | Hover state accent |

### Neutrals

| Token | Hex | OKLCH | Usage |
|-------|-----|-------|-------|
| `--color-ink` | `#1A1A1A` | oklch(15% 0 0) | Основной текст на светлом фоне |
| `--color-ink-secondary` | `#5C5C5C` | oklch(42% 0 0) | Вторичный текст, цены |
| `--color-ink-muted` | `#8C8C8C` | oklch(58% 0 0) | Placeholder, consent text |
| `--color-surface` | `#FFFFFF` | oklch(100% 0 0) | Фон карточек, основной контент |
| `--color-bg` | `#F5F3EF` | oklch(96% 0.002 90) | Фон секций — тёплый бежевый |
| `--color-bg-dark` | `#1C2833` | oklch(22% 0.02 250) | Hero-секция, тёмный фон |
| `--color-bg-footer` | `#141B22` | oklch(15% 0.02 250) | Футер — самый тёмный |

### Semantic

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-success` | `#4CAF50` | Успех, Telegram-блок |
| `--color-rating` | `#3B82F6` | Бейдж рейтинга 5,0 |
| `--color-online` | `#10B981` | Бейдж «Только онлайн» |

### Contrast Ratios (WCAG AA compliance)

- Ink (#1A1A1A) on Surface (#FFFFFF): **16.8:1** ✅ AAA
- Ink-secondary (#5C5C5C) on Surface (#FFFFFF): **5.7:1** ✅ AA
- Ink-muted (#8C8C8C) on Surface (#FFFFFF): **3.6:1** ❌ (use only for ≥18px or decorative)
- Primary (#2E7D5F) on Surface (#FFFFFF): **4.1:1** ⚠️ borderline AA (consider `#23684D` for text)

## Typography

### Font Stack

Tilda загружает кастомные шрифты через CDN. Рекомендуемая замена для собственной разработки:

```css
--font-display: 'Formular', 'Futura PT', -apple-system, BlinkMacSystemFont, sans-serif;
--font-body: 'Formular', 'Futura PT', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

Счётчик font-family: 2 (display + mono). Основной шрифт — геометрический гротеск с характером.

### Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display | clamp(2.5rem, 5vw, 4.5rem) | 700 | 1.1 | Hero-заголовок |
| h1 | clamp(2rem, 4vw, 3rem) | 700 | 1.2 | Заголовок страницы |
| h2 | clamp(1.5rem, 3vw, 2.25rem) | 700 | 1.25 | Заголовок секции |
| h3 | 1.25rem (20px) | 600 | 1.3 | Имя специалиста |
| h4 | 1rem (16px) | 600 | 1.4 | Специализация |
| body | 1rem (16px) | 400 | 1.6 | Основной текст |
| body-sm | 0.875rem (14px) | 400 | 1.5 | Описания, ответы FAQ |
| caption | 0.75rem (12px) | 400 | 1.4 | Consent, мета-информация |
| caption-xs | 0.6875rem (11px) | 400 | 1.3 | «Займет менее 1 минуты» |

Scale ratio между шагами: ≥1.25 (major third).

### Typography Rules

- `text-wrap: balance` на h1–h3
- `text-wrap: pretty` на body-тексте >3 строк
- Max line length: 65–75ch для body
- Letter-spacing display: ≥ -0.04em (floor)
- Без all-caps в body-тексте
- Uppercase только для label ≤4 слов и badge

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
```

### Application

| Context | Value |
|---------|-------|
| Section padding vertical | `--space-2xl` (64px) |
| Container max-width | 1200px |
| Card gap (grid) | `--space-md` (24px) |
| Card padding | `--space-lg` (32px) |
| Button padding (vertical) | `--space-xs`–`--space-sm` (12–16px) |
| Button padding (horizontal) | `--space-md`–`--space-lg` (24–32px) |
| FAQ item gap | `--space-md` (24px) |
| Nav item gap | `--space-md` (24px) |

## Border Radius

```css
--radius-sm: 4px;   /* Form inputs */
--radius-md: 8px;   /* Buttons, images */
--radius-lg: 16px;  /* Cards */
--radius-full: 9999px; /* Avatars */
```

## Shadows

```css
--shadow-card: 0 2px 10px rgba(0, 0, 0, 0.08);
--shadow-card-hover: 0 4px 20px rgba(0, 0, 0, 0.12);
--shadow-button-hover: 0 4px 15px rgba(46, 125, 95, 0.3);
--shadow-header: 0 1px 4px rgba(0, 0, 0, 0.05);
```

## Motion

```css
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 400ms;
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
```

### Transitions

| Element | Property | Duration | Easing |
|---------|----------|----------|--------|
| Buttons | background, transform, box-shadow | 200ms | ease-out |
| Cards hover | transform: translateY(-4px) | 300ms | ease-out |
| Mobile menu | transform (slide) | 300ms | ease-in-out |
| Modal/popup | opacity, transform (scale+fade) | 300ms | ease-in-out |
| Filter tabs | color, background | 200ms | ease-out |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Component Library

### Buttons

| Variant | Background | Text | Radius | Usage |
|---------|-----------|------|--------|-------|
| Primary | `--color-primary` | white | `--radius-md` | «Записаться», основные CTA |
| Accent | `--color-accent` | `--color-ink` | `--radius-md` | «Подобрать специалиста» (quiz) |
| Outline | transparent | white | `--radius-md` | На тёмном фоне (hero, footer) |
| Secondary | transparent | `--color-primary` | `--radius-md` | «О специалисте» |

Minimum touch target: 44×44px.

### Cards (Specialist)

```
┌──────────────────────────┐
│ [Photo / Placeholder]     │
│                           │
│ [Badge: Кандидат наук]    │
│                           │
│ Name (h3, 20px, 600)     │
│ Title · N лет (body-sm)   │
│                           │
│ Description (body-sm)     │
│                           │
│ Цена · ₽ (body, muted)   │
│                           │
│ [Записаться] [О спец-те]  │
└──────────────────────────┘
```

### Badges

| Variant | Background | Text | Icon |
|---------|-----------|------|------|
| Achievement | `--color-accent` | `--color-ink` | — |
| Online | `--color-online` | white | — |
| Rating | `--color-rating` | white | ⭐ |

### Form Fields

```css
--input-bg: var(--color-surface);
--input-border: 1px solid #D1D5DB;
--input-border-focus: 2px solid var(--color-primary);
--input-radius: var(--radius-sm);
--input-padding: 12px 16px;
--input-font: var(--font-body);
```

Labels сверху, error state с красной обводкой + текст ошибки под полем.

### Navigation

Desktop: горизонтальная, логотип слева, ссылки по центру, CTA справа.
Mobile: hamburger → slide-in меню слева (300ms ease-in-out).

**Breakpoints:**
- Desktop: ≥1024px
- Tablet: 768px–1023px
- Mobile: <768px (single column, stacked)

### Filter Tabs (Специалисты)

Горизонтальный ряд кнопок-фильтров. Активный: залитый цвет (`--color-primary`), неактивный: outline.
JS-фильтрация карточек без перезагрузки.

### FAQ Accordion

Вопросы — clickable с иконкой раскрытия (± или ▼). Ответ — раскрывающийся блок с `max-height` анимацией.

### Floating Chat Buttons

Фиксированный блок в правом нижнем углу: Telegram, WhatsApp, VK, звонок. Иконки в кругах, gap 8–12px, z-index поверх контента.

## Assets

| Asset | URL | Format |
|-------|-----|--------|
| Logo | `static.tildacdn.com/.../Frame.svg` | SVG |
| Icons | `static.tildacdn.com/.../Group_*.svg` | SVG |
| Photos | `thb.tildacdn.com/.../empty/*.jpg` | JPEG (placeholder) |

При собственной разработке: логотип пересоздать в векторе, иконки заменить на Lucide или Phosphor, фото специалистов загрузить в webp/avif.
