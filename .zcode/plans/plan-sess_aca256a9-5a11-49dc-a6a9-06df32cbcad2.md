# План: Приведение чата к дизайн-системе

## Проблема
Чат использует border-radius 20px, неправильные отступы, мелкий шрифт. Отчёты по ссылке выглядят отлично (сделаны по дизайн-системе), а чат — бардак.

## Что меняем (только CSS, не трогая JS)

### 1. Border-radius: 20px → 4px везде
- message-bubble: 20px → 4px (кроме bottom-left/right corners — 2px)
- input field: 20px → 4px
- progress bubble: 20px → 4px
- Все остальные 10px, 12px, 16px → 4px

### 2. Message bubbles: больше воздуха
- padding: 16px 20px → 20px 24px
- max-width: 75% → 85% (читаемее)

### 3. Section labels: по дизайн-системе
- Уже ОК (accent color, uppercase) — оставить

### 4. Stat cards: уже починили — оставить

### 5. Surface blocks: больше отступов
- padding: 10px 14px → 16px 20px
- margin: 8px → 12px

### 6. Tables: по дизайн-системе
- th: uppercase, 11px, letter-spacing
- td: больше padding

### 7. Убрать «склеенность»
- Между блоками — больше margin
- Между параграфами — больше line-height

## Подход
Только CSS правки в `<style>` секции chat-inline.php. **Не трогать JS** — это сломало его в прошлый раз.

## Файл
`AIM/theme/chat-inline.php` — CSS секция (строки 1-893)
