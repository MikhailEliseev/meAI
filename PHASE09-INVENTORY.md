# Phase 09 — Inventory & Integration Plan

**Дата анализа:** 2026-06-28 07:47 МСК
**Статус на сервере:** Phase 09 файлы полностью отсутствуют (удалены при откате)
**Backup:** `~/Desktop/phase09-COMPLETE-20260628-022838.tar.gz` (446 KB)

---

## Что добавляет Phase 09

### 1. Phase Tracker — Визуализация 8 фаз пресейла

**Файл:** `chat-inline-pro.php` (22462 bytes)

**Что это:**
- Панель с 8 фазами пресейла (grid 2x4)
- Отслеживание прогресса в реальном времени
- Автоматическое обнаружение фаз из tool-progress events

**8 фаз:**
1. Анализ сайта (run_prescan)
2. Финансы из ФНС (find_company_financials)
3. Врачи и соцсети (find_doctor_handles, run_instagram_content)
4. Конкуренты (find_competitors, run_ci_analysis)
5. Отзывы пациентов (run_review_platforms, run_forum_pains)
6. СМИ и медийность (run_media_urls)
7. Технический аудит (run_tech_seo_audit, run_seo_audit, run_lighthouse)
8. Генерация отчёта (generate_html_report)

**Состояния фаз:**
- `.pending` — не начата (opacity: 0.4, серый)
- `.working` — в процессе (border accent, spinner icon, pulse анимация)
- `.done` — завершена (зелёная галочка, success цвет)

**Счётчики:**
- Прогресс: "3/8" в заголовке панели
- Live counters в каждой фазе: "5 конкурентов", "12 врачей", "8 отзывов"

**Mapping stage → phase:**
```javascript
const STAGE_TO_PHASE = {
    'run_prescan': 1, 'prescan': 1,
    'find_company_financials': 2, 'financials': 2, 'finance': 2,
    'find_doctor_handles': 3, 'doctors': 3, 'run_instagram_content': 3, 'instagram': 3,
    'find_competitors': 4, 'competitors': 4, 'run_ci_analysis': 4, 'ci_analysis': 4,
    'run_review_platforms': 5, 'reviews': 5, 'run_forum_pains': 5, 'forum_pains': 5,
    'run_media_urls': 6, 'media': 6, 'smi': 6,
    'run_tech_seo_audit': 7, 'tech_seo': 7, 'run_seo_audit': 7, 'seo': 7, 'run_lighthouse': 7,
    'generate_html_report': 8, 'html_report': 8, 'report': 8,
};
```

**Интеграция:**
- `window.aimProTrackPhase(stage, message)` — вызывается из существующего чата
- Детектит фазу по stage из tool-progress события
- Парсит счётчики из message текста (regex: `/(\d+)\s+(конкурент|врач|отзыв|упоминани|страниц|стат)/i`)

---

### 2. Report Preview Card — WOW момент

**Что это:**
- Карточка с превью готового отчёта
- Показывается после завершения всех 8 фаз
- Reveal анимация (scale + fadeIn)

**Содержимое:**
- Badge "✓ Отчёт готов" (зелёный)
- Заголовок отчёта (Playfair Display)
- 3 статистики в grid (value + label)
- Две кнопки CTA:
  - Primary: "Открыть полный отчёт →" (accent button, ссылка на HTML)
  - Secondary: "Прислать на почту/TG" (показывает fallback форму)

**Интеграция:**
- `window.aimProShowReport(reportData)` — вызывается когда Hermes возвращает готовый отчёт
- reportData: `{ url, title, client, stats: [{value, label}, ...] }`

---

### 3. Fallback Form — Email/Telegram сбор

**Что это:**
- Форма для сбора контакта пользователя, если он хочет уйти до завершения
- Отправляет контакт на сервер + в Telegram админу

**UX Flow:**
1. Пользователь нажимает "Прислать на почту/TG"
2. Появляется форма с input (email или @telegram)
3. Submit → POST `/wp-json/aim/v1/fallback`
4. Показывается success message

**Backend endpoint:** `aim-pro-endpoints.php`
- Валидирует email/telegram
- Сохраняет в `wp_options` (max 100 записей)
- Отправляет уведомление админу в Telegram
- Отправляет email админу
- Если email + report_url готов → отправляет отчёт пользователю сразу

**Данные сохраняются:**
```php
[
    'contact' => 'user@example.com',
    'type' => 'email|telegram|other',
    'session_id' => 'hermes-session-id',
    'report_url' => 'https://iamaim.ru/...',
    'timestamp' => 1719556842,
    'created_at' => '2026-06-28 07:47:22',
    'ip' => '1.2.3.4',
    'user_agent' => 'Mozilla/5.0 ...',
]
```

---

## Текущее состояние сервера

**WordPress тема:** `/var/www/iamaim.ru/wp-content/themes/aim-theme/`

**Что есть:**
- ✅ `functions.php` (21K, June 13 23:16) — старая версия без include aim-pro-endpoints.php
- ✅ `chat/hermes-chat.html` (13K) — текущий чат (без Phase 09 фич)
- ❌ `chat-inline-pro.php` — отсутствует
- ❌ `aim-pro-endpoints.php` — отсутствует

**Что используется сейчас:**
- Чат: `/chat/hermes-chat.html` — standalone HTML с встроенным JS
- Design: Dual Theme CSS variables (light/dark) — совпадает с Phase 09
- SSE streaming: подключается к `/api/chat/stream` (FastAPI Hermes)
- Tool progress: обрабатывается в JS чата, но БЕЗ Phase Tracker UI

---

## План интеграции

### Принципиальное решение

**НЕ ТРОГАТЬ существующий `hermes-chat.html`** — он работает, стабилен, дизайн эталонный.

**Создать НОВЫЙ чат `hermes-chat-pro.html`** с Phase 09 фичами:
1. Скопировать `hermes-chat.html` как основу
2. Добавить Phase Tracker панель
3. Добавить Report Preview карточку
4. Добавить Fallback Form
5. Подключить JS integration hooks

**Создать `aim-pro-endpoints.php`** для fallback endpoint.

**Обновить `functions.php`** — добавить `include aim-pro-endpoints.php`.

**Frontend роутинг:**
- По умолчанию: `/` загружает `hermes-chat.html` (старый чат)
- Опционально: `/?pro=1` загружает `hermes-chat-pro.html` (новый чат с Phase 09)
- После тестирования: переключить дефолт на pro версию

---

## Backend поддержка — что нужно в Hermes

### 1. Tool-progress events с stage field

**Текущее состояние:** Проверить как Hermes отправляет tool-progress через SSE.

**Нужно:**
```javascript
{
    type: 'tool-progress',
    message: 'Найдено 5 конкурентов',
    stage: 'find_competitors',  // <-- это поле критично
    progress: 60,
}
```

**Где это устанавливается:** `AIM/hermes/app/tools/*.py` в функции `push_tool_progress()`

**Проверка:** Посмотреть код `push_tool_progress()` в `main.py` или `agent_wrapper.py`.

---

### 2. Report URL в финальном ответе

**Нужно:**
Когда Hermes возвращает финальный ответ с готовым отчётом, он должен включить:
```javascript
{
    type: 'message',
    content: 'Готово! Отчёт сгенерирован.',
    report_url: 'https://iamaim.ru/wp-json/aim/v1/session/<hash>',
    report_title: 'Разведка клиники XYZ',
    stats: [
        { value: '5', label: 'Конкурентов' },
        { value: '12', label: 'Врачей' },
        { value: '8', label: 'Отзывов' },
    ]
}
```

**Где:** В коде генерации финального ответа после `generate_html_report` tool.

---

### 3. Fallback endpoint access

**Endpoint:** `POST /wp-json/aim/v1/fallback`

**Доступен:** Да, если `aim-pro-endpoints.php` подключён к `functions.php`.

**Hermes не трогать** — fallback форма работает полностью на WordPress стороне.

---

## Последовательность действий

### Phase 1: Проверка Hermes backend

1. ✅ Проверить `push_tool_progress()` — передаёт ли `stage` параметр
2. ✅ Проверить финальный ответ — включает ли `report_url` и stats
3. Если НЕТ — добавить эти поля

### Phase 2: Создать WordPress файлы

1. ✅ Скопировать `chat/hermes-chat.html` → `chat/hermes-chat-pro.html`
2. ✅ Внедрить Phase Tracker панель из `chat-inline-pro.php`
3. ✅ Внедрить Report Preview карточку
4. ✅ Внедрить Fallback Form
5. ✅ Добавить JS integration hooks:
   - `window.aimProTrackPhase(stage, message)` в tool-progress handler
   - `window.aimProShowReport(reportData)` когда пришёл финальный ответ с report_url

### Phase 3: Backend endpoints

1. ✅ Скопировать `aim-pro-endpoints.php` на сервер
2. ✅ Обновить `functions.php` — добавить `include_once get_template_directory() . '/aim-pro-endpoints.php';`
3. ✅ Настроить Telegram bot token и admin chat ID в wp_options или .env

### Phase 4: Deployment

1. ✅ Закоммитить все изменения локально
2. ✅ Деплой на сервер через `docker cp` или rsync
3. ✅ Перезагрузить WordPress (если нужно)
4. ✅ Протестировать fallback endpoint: `curl -X POST https://iamaim.ru/wp-json/aim/v1/fallback -H "Content-Type: application/json" -d '{"contact":"test@test.com"}'`

### Phase 5: Testing

1. ✅ Открыть `https://iamaim.ru/?pro=1` (pro версия чата)
2. ✅ Запустить пресейл с тестовым URL
3. ✅ Проверить что Phase Tracker активируется и обновляется
4. ✅ Проверить что счётчики появляются
5. ✅ Дождаться окончания пресейла — проверить Report Preview
6. ✅ Проверить Fallback Form — отправить email/telegram, проверить что пришло уведомление админу

### Phase 6: Switch to default

1. ✅ Если всё работает — переименовать `hermes-chat.html` → `hermes-chat-legacy.html`
2. ✅ Переименовать `hermes-chat-pro.html` → `hermes-chat.html`
3. ✅ Теперь Phase 09 версия загружается по умолчанию

---

## Критические точки

### 1. Не сломать дизайн

**Проблема:** Phase 09 может внести визуальные конфликты.

**Решение:**
- Использовать существующие CSS variables (Dual Theme)
- Phase Tracker, Report Preview, Fallback Form изолированы в `.aim-chat-pro-scope`
- Все стили Phase 09 используют те же переменные что и `hermes-chat.html`

### 2. Stage detection

**Проблема:** Hermes может не передавать `stage` в tool-progress.

**Решение:**
- Добавить fallback: если нет `stage`, парсить из `message` (например "run_prescan completed")
- Расширенный mapping включает substring match

### 3. Report URL timing

**Проблема:** Report URL может быть недоступен сразу.

**Решение:**
- Report Preview показывается только когда `report_url` установлен
- Fallback форма работает и БЕЗ report_url — просто сохраняет контакт для последующей отправки

---

## Тестовые сценарии

### Test 1: Phase Tracker

1. Открыть `/?pro=1`
2. Отправить URL клиники
3. Наблюдать:
   - Phase Tracker появляется при первом tool-progress
   - Фазы меняют состояние: pending → working → done
   - Счётчик "X/8" обновляется
   - Live counters появляются (если есть в message)

### Test 2: Report Preview

1. Дождаться завершения пресейла
2. Наблюдать:
   - Report Preview карточка появляется с reveal анимацией
   - Заголовок и статистики заполнены
   - Кнопка "Открыть отчёт" работает (новая вкладка)
   - Все 8 фаз помечены как done

### Test 3: Fallback Form

1. Нажать "Прислать на почту/TG" (до или после завершения)
2. Ввести email: `test@example.com`
3. Submit
4. Наблюдать:
   - Success message появляется
   - Админ получил уведомление в Telegram
   - Админ получил email
   - Если отчёт готов — пользователь получил email с ссылкой

---

## Откат

Если Phase 09 сломает что-то:

```bash
# На сервере
ssh aim
cd /var/www/iamaim.ru/wp-content/themes/aim-theme/chat/

# Вернуть старый чат
cp hermes-chat-legacy.html hermes-chat.html

# Удалить Phase 09 файлы
rm hermes-chat-pro.html

# Откатить functions.php (удалить строку include aim-pro-endpoints)
nano /var/www/iamaim.ru/wp-content/themes/aim-theme/functions.php

# Перезагрузить WordPress (опционально)
docker compose -f /opt/aim/AIM/docker-compose.yml restart aim-wordpress
```

---

## Следующий шаг

Начать с **Phase 1: Проверка Hermes backend** — проверить код `push_tool_progress()` и финального ответа.
