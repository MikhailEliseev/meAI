# Phase 09 Integration Plan — Homepage Chat Widget

**Дата анализа:** 2026-06-28 10:40 МСК
**Статус:** Examination Complete — Ready for Implementation Approval
**Цель:** Добавить Phase Tracker, Report Preview, Fallback Form в React-виджет главной страницы БЕЗ изменения дизайна

---

## Текущая архитектура React-чата

### Структура компонентов

```
HermesChat (index.jsx) — корневой компонент
├── useStreamChat() — custom hook для SSE streaming
├── EmptyChat — пустое состояние с промо + quick actions
├── ChatBubble — сообщение (user/agent)
└── ChatInput — textarea + send/stop кнопки
```

### Файлы и их роль

| Файл | Строк | Роль |
|------|-------|------|
| `src/index.jsx` | 59 | Корневой HermesChat компонент, условный рендеринг EmptyChat vs message list |
| `src/useStreamChat.js` | 196 | SSE streaming hook, обработка events, session management |
| `src/components/ChatBubble.jsx` | 49 | Рендер одного сообщения с аватаром, timestamp, streaming indicator |
| `src/components/ChatInput.jsx` | 59 | Textarea с auto-resize, Enter to send, stop button при streaming |
| `src/components/EmptyChat.jsx` | 69 | Hero section с промо, input, quick actions, trust badges |
| `src/chat.css` | 31 | Минимальная изоляция стилей, fadeIn/slideUp анимации |

### Ключевые особенности

**SSE Event Handling (useStreamChat.js:116-144):**
```javascript
switch (event.type) {
  case 'text-delta':
    fullTextRef.current += event.textDelta;
    break;
  case 'finish':
    setSessionId(event.session_id);
    break;
  case 'error':
    fullTextRef.current = event.message || 'Ошибка';
    break;
  // step-start, step-end, tool-progress — silently ignored (line 143)
}
```

**Проблема:** `tool-progress` события игнорируются → Phase Tracker не может работать.

**Styling:**
- Tailwind CSS классы (bg-surface-2, border-border-hairline, text-ink)
- CSS variables из родительской темы WordPress: --bg, --surface, --accent, --text-*
- Анимации через @keyframes (fadeIn, chatSlideUp)

**State Management:**
- `useState` для messages, status, sessionId
- `useRef` для streamingRef (текущий текст агента), abortControllerRef (остановка SSE)
- localStorage для sessionId (LS_SESSION_KEY = 'hermes-session-id')

---

## Что нужно добавить (Phase 09 Features)

### 1. Phase Tracker Panel

**Вид:** Панель с 8 фазами в grid 2x4, каждая фаза = карточка с иконкой, названием, состоянием.

**Состояния фаз:**
- `.pending` — opacity: 0.4, серый цвет
- `.working` — border accent, spinner icon, pulse анимация
- `.done` — зелёная галочка, success цвет

**Счётчики:**
- Прогресс в заголовке: "3/8"
- Live counters в каждой фазе: "5 конкурентов", "12 врачей"

**Данные:**
```javascript
const PHASES = [
  { id: 1, name: 'Анализ сайта', icon: '🔍', stages: ['run_prescan', 'prescan'] },
  { id: 2, name: 'Финансы', icon: '💰', stages: ['find_company_financials', 'financials', 'finance'] },
  { id: 3, name: 'Врачи и соцсети', icon: '👨‍⚕️', stages: ['find_doctor_handles', 'doctors', 'run_instagram_content', 'instagram'] },
  { id: 4, name: 'Конкуренты', icon: '🎯', stages: ['find_competitors', 'competitors', 'run_ci_analysis', 'ci_analysis'] },
  { id: 5, name: 'Отзывы', icon: '⭐', stages: ['run_review_platforms', 'reviews', 'run_forum_pains', 'forum_pains'] },
  { id: 6, name: 'СМИ', icon: '📰', stages: ['run_media_urls', 'media', 'smi'] },
  { id: 7, name: 'Технический аудит', icon: '⚙️', stages: ['run_tech_seo_audit', 'tech_seo', 'run_seo_audit', 'seo', 'run_lighthouse'] },
  { id: 8, name: 'Отчёт', icon: '📊', stages: ['generate_html_report', 'html_report', 'report'] },
];
```

**Интеграция:**
- Новый компонент: `src/components/PhaseTracker.jsx`
- Добавить в `useStreamChat.js`: обработка `tool-progress` events
- State: `const [phases, setPhases] = useState(PHASES.map(p => ({ ...p, status: 'pending', counter: null })))`
- Update function: `updatePhase(stage, message)` — детектит фазу по stage, обновляет status, парсит counter из message

### 2. Report Preview Card

**Вид:** WOW-карточка с badge "✓ Отчёт готов", заголовком, 3 статистиками, 2 кнопками CTA.

**Данные:**
```javascript
{
  url: 'https://iamaim.ru/wp-json/aim/v1/session/abc123',
  title: 'Разведка клиники XYZ',
  stats: [
    { value: '5', label: 'Конкурентов' },
    { value: '12', label: 'Врачей' },
    { value: '8', label: 'Отзывов' },
  ]
}
```

**Триггер:** Когда `finish` event содержит `report_url` (уже реализовано в Hermes backend).

**Интеграция:**
- Новый компонент: `src/components/ReportPreview.jsx`
- Добавить в `useStreamChat.js`: обработка `finish` event с `report_url`
- State: `const [reportData, setReportData] = useState(null)`
- Рендер: `{reportData && <ReportPreview data={reportData} onRequestEmail={() => setShowFallback(true)} />}`

### 3. Fallback Form

**Вид:** Модальная форма с input (email или @telegram), submit кнопка, success animation.

**Backend endpoint:** `POST /wp-json/aim/v1/fallback` (уже развёрнут в aim-pro-endpoints.php)

**UX Flow:**
1. Пользователь нажимает "Прислать на почту/TG" (secondary CTA в ReportPreview)
2. Появляется форма с input
3. Submit → POST request → success message

**Интеграция:**
- Новый компонент: `src/components/FallbackForm.jsx`
- State: `const [showFallback, setShowFallback] = useState(false)`
- Рендер: `{showFallback && <FallbackForm sessionId={sessionId} reportUrl={reportData?.url} onClose={() => setShowFallback(false)} />}`

---

## Изменения в существующих файлах

### useStreamChat.js

**Добавить:**
1. Phase tracking state:
```javascript
const [phases, setPhases] = useState(PHASES.map(p => ({ ...p, status: 'pending', counter: null })));

function updatePhase(stage, message) {
  const phase = PHASES.find(p => p.stages.includes(stage));
  if (!phase) return;

  setPhases(prev => prev.map(p => {
    if (p.id !== phase.id) return p;

    // Extract counter from message: "Найдено 5 конкурентов" → "5 конкурентов"
    const counterMatch = message.match(/(\d+)\s+(конкурент|врач|отзыв|упоминани|страниц|стат)/i);
    const counter = counterMatch ? `${counterMatch[1]} ${counterMatch[2]}` : null;

    return { ...p, status: 'working', counter };
  }));
}
```

2. Report data state:
```javascript
const [reportData, setReportData] = useState(null);
```

3. Event handler modification (lines 116-144):
```javascript
case 'tool-progress':
  if (event.stage && event.message) {
    updatePhase(event.stage, event.message);
  }
  break;

case 'finish':
  if (event.session_id) {
    setSessionId(event.session_id);
    try { localStorage.setItem(LS_SESSION_KEY, event.session_id); } catch {}
  }

  // Phase 09: Extract report data
  if (event.report_url) {
    setReportData({
      url: event.report_url,
      title: event.report_title || 'Разведка пресейла',
      stats: extractStatsFromSession(event), // helper function
    });

    // Mark all phases as done
    setPhases(prev => prev.map(p => ({ ...p, status: 'done' })));
  }
  break;
```

4. Return phases and reportData:
```javascript
return {
  messages,
  sendMessage,
  stop,
  status,
  streamingRef,
  phases,          // NEW
  reportData,      // NEW
};
```

### index.jsx

**Добавить:**
1. Import новых компонентов:
```javascript
import { PhaseTracker } from './components/PhaseTracker';
import { ReportPreview } from './components/ReportPreview';
import { FallbackForm } from './components/FallbackForm';
```

2. Destructure новых полей из hook:
```javascript
const { messages, sendMessage, stop, status, streamingRef, phases, reportData } = useStreamChat();
```

3. Fallback state:
```javascript
const [showFallback, setShowFallback] = useState(false);
```

4. Рендер Phase 09 компонентов (AFTER message list, BEFORE ChatInput):
```javascript
{hasMessages && (
  <>
    {/* Phase Tracker appears when first tool-progress event arrives */}
    {phases.some(p => p.status !== 'pending') && (
      <PhaseTracker phases={phases} />
    )}

    {/* Report Preview appears when finish event contains report_url */}
    {reportData && (
      <ReportPreview
        data={reportData}
        onRequestEmail={() => setShowFallback(true)}
      />
    )}

    {/* Fallback Form modal */}
    {showFallback && (
      <FallbackForm
        sessionId={sessionId}
        reportUrl={reportData?.url}
        onClose={() => setShowFallback(false)}
      />
    )}
  </>
)}
```

---

## Новые компоненты (детальные спецификации)

### PhaseTracker.jsx

```javascript
import React from 'react';

export function PhaseTracker({ phases }) {
  const completedCount = phases.filter(p => p.status === 'done').length;
  const totalCount = phases.length;

  return (
    <div className="w-full max-w-3xl mx-auto px-4 mb-6">
      <div className="bg-surface-2 border border-border-hairline rounded-lg overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border-hairline flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${completedCount === totalCount ? 'bg-green-500' : 'bg-accent animate-pulse'}`} />
          <span className="font-semibold text-ink">Прогресс пресейла</span>
          <span className="text-text-muted text-sm ml-auto">{completedCount}/{totalCount}</span>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-border-hairline p-px">
          {phases.map(phase => (
            <PhaseCard key={phase.id} phase={phase} />
          ))}
        </div>
      </div>
    </div>
  );
}

function PhaseCard({ phase }) {
  const isPending = phase.status === 'pending';
  const isWorking = phase.status === 'working';
  const isDone = phase.status === 'done';

  return (
    <div className={`bg-surface-2 p-4 flex flex-col gap-2 transition-opacity ${isPending ? 'opacity-40' : 'opacity-100'}`}>
      <div className="flex items-center gap-2">
        <span className="text-2xl">{phase.icon}</span>
        {isWorking && <Spinner />}
        {isDone && <CheckIcon />}
      </div>
      <span className="text-xs font-medium text-ink">{phase.name}</span>
      {phase.counter && (
        <span className="text-xs text-text-muted">{phase.counter}</span>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg className="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}
```

### ReportPreview.jsx

```javascript
import React from 'react';

export function ReportPreview({ data, onRequestEmail }) {
  return (
    <div className="w-full max-w-3xl mx-auto px-4 mb-6" style={{animation: 'fadeIn 0.5s ease-out'}}>
      <div className="bg-surface-2 border border-border-hairline rounded-lg p-6">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-green-500/10 text-green-600 px-3 py-1 rounded-full text-xs font-medium mb-4">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Отчёт готов
        </div>

        {/* Title */}
        <h3 className="text-xl font-bold text-ink mb-4">{data.title}</h3>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {data.stats.map((stat, i) => (
            <div key={i} className="text-center">
              <div className="text-2xl font-bold text-accent">{stat.value}</div>
              <div className="text-xs text-text-muted mt-1">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex gap-3">
          <a
            href={data.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 bg-accent text-white text-center px-4 py-3 rounded-lg text-sm font-medium hover:brightness-110 transition-all"
          >
            Открыть полный отчёт →
          </a>
          <button
            onClick={onRequestEmail}
            className="flex-1 bg-surface-3 text-ink text-center px-4 py-3 rounded-lg text-sm font-medium border border-border-hairline hover:bg-surface-2 transition-all"
          >
            Прислать на почту/TG
          </button>
        </div>
      </div>
    </div>
  );
}
```

### FallbackForm.jsx

```javascript
import React, { useState } from 'react';

export function FallbackForm({ sessionId, reportUrl, onClose }) {
  const [contact, setContact] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!contact.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/wp-json/aim/v1/fallback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contact: contact.trim(),
          session_id: sessionId,
          report_url: reportUrl || '',
        }),
      });

      if (!res.ok) throw new Error('Network error');

      const data = await res.json();
      if (!data.ok) throw new Error(data.message || 'Unknown error');

      setSuccess(true);
      setTimeout(onClose, 2000);
    } catch (err) {
      setError(err.message || 'Ошибка отправки');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4" onClick={onClose}>
      <div className="bg-surface-2 border border-border-hairline rounded-lg p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
        {success ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-ink mb-2">Отлично!</h3>
            <p className="text-sm text-text-muted">Отчёт будет отправлен после завершения анализа</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <h3 className="text-lg font-bold text-ink mb-4">Получить отчёт на почту или в Telegram</h3>
            <input
              type="text"
              value={contact}
              onChange={e => setContact(e.target.value)}
              placeholder="email@example.com или @telegram"
              className="w-full bg-bg border border-border-hairline rounded-lg px-4 py-3 text-sm text-ink placeholder:text-text-subtle focus:outline-none focus:border-accent transition-colors mb-4"
              disabled={loading}
              autoFocus
            />
            {error && (
              <p className="text-sm text-red-500 mb-4">{error}</p>
            )}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-surface-3 text-ink px-4 py-3 rounded-lg text-sm font-medium hover:bg-surface-2 transition-all"
                disabled={loading}
              >
                Отмена
              </button>
              <button
                type="submit"
                className="flex-1 bg-accent text-white px-4 py-3 rounded-lg text-sm font-medium hover:brightness-110 transition-all disabled:opacity-50"
                disabled={loading || !contact.trim()}
              >
                {loading ? 'Отправка...' : 'Отправить'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
```

---

## CSS Additions

**Добавить в chat.css:**

```css
/* Phase Tracker animations */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Report Preview reveal */
@keyframes revealUp {
  from { opacity: 0; transform: translateY(30px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Fallback Form backdrop */
#hermes-chat .fallback-backdrop {
  backdrop-filter: blur(4px);
}
```

---

## Build & Deploy Process

### 1. Local Development
```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/theme/chat/
npm run build  # esbuild compiles src/ → dist/chat-bundle.js
```

### 2. Test Locally
Открыть `https://iamaim.ru` с live bundle (если настроен dev proxy) или скопировать bundle на сервер для теста.

### 3. Deploy to Server
```bash
# Copy bundle to server
scp dist/chat-bundle.js aim:/var/www/iamaim.ru/wp-content/themes/aim-theme/chat/

# OR via rsync
rsync -avz dist/ aim:/var/www/iamaim.ru/wp-content/themes/aim-theme/chat/dist/
```

### 4. Verify
- Открыть `https://iamaim.ru`
- Отправить URL клиники
- Проверить:
  - Phase Tracker появляется при первом tool-progress
  - Фазы меняют состояние: pending → working → done
  - Счётчик "X/8" обновляется
  - Report Preview появляется после finish event с report_url
  - Fallback Form работает (submit → success)

---

## Rollback Plan

Если Phase 09 ломает чат:

```bash
# 1. Откатить bundle
ssh aim
cd /var/www/iamaim.ru/wp-content/themes/aim-theme/chat/dist/
cp chat-bundle.js.backup chat-bundle.js  # backup создан перед деплоем

# 2. Очистить браузерный кэш
# Ctrl+Shift+R на https://iamaim.ru

# 3. Если нужно — откатить коммит
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/
git log --oneline AIM/theme/chat/
git revert <commit-hash>
```

---

## Testing Checklist

### Phase Tracker
- [ ] Появляется при первом tool-progress event
- [ ] Фазы меняют состояние: pending → working → done
- [ ] Счётчик "3/8" обновляется корректно
- [ ] Live counters появляются ("5 конкурентов", "12 врачей")
- [ ] Spinner анимация работает в working состоянии
- [ ] Зелёная галочка появляется в done состоянии

### Report Preview
- [ ] Появляется после finish event с report_url
- [ ] Badge "✓ Отчёт готов" отображается
- [ ] Заголовок и статистики заполнены корректно
- [ ] Кнопка "Открыть полный отчёт" открывает новую вкладку с report_url
- [ ] Кнопка "Прислать на почту/TG" показывает Fallback Form
- [ ] Reveal анимация плавная

### Fallback Form
- [ ] Модальное окно открывается по клику на вторичный CTA
- [ ] Input принимает email и @telegram
- [ ] Validation работает (не пустое значение)
- [ ] Submit отправляет POST /wp-json/aim/v1/fallback
- [ ] Success animation показывается после успешной отправки
- [ ] Modal закрывается через 2 секунды или по клику "Отмена"
- [ ] Error state показывается при ошибке сети

### Edge Cases
- [ ] Чат работает если tool-progress events НЕ приходят (Phase Tracker просто не появляется)
- [ ] Чат работает если finish event БЕЗ report_url (Report Preview не появляется)
- [ ] Fallback Form работает БЕЗ report_url (просто сохраняет контакт для последующей отправки)
- [ ] Multiple sessions: Phase Tracker сбрасывается при новой сессии
- [ ] Browser refresh: session_id восстанавливается из localStorage, но phases state теряется (это ОК)

---

## Known Limitations

1. **Phase Tracker state не персистится** — при перезагрузке страницы прогресс теряется. Это ОК, так как пресейл обычно выполняется за один сеанс (2-5 минут).

2. **Нет resume функциональности** — если пользователь закрыл страницу и вернулся позже, Phase Tracker начнётся с нуля. Для resume нужен отдельный endpoint `GET /wp-json/aim/v1/session/<session_id>/progress` который возвращает текущее состояние фаз (это BACKLOG).

3. **Stats в Report Preview могут быть пустыми** — если Hermes не вернёт статистики в finish event, будет показан только report_url и title. Для полных статистик нужно добавить их в Hermes backend (это BACKLOG).

4. **Telegram notifications требуют ручной настройки** — `aim_telegram_bot_token` и `aim_telegram_admin_chat_id` должны быть установлены в WordPress options. Без них Fallback Form работает, но уведомления админу не приходят.

---

## Next Steps

**Когда получить approval от пользователя:**

1. Создать новые компоненты: `PhaseTracker.jsx`, `ReportPreview.jsx`, `FallbackForm.jsx`
2. Модифицировать `useStreamChat.js`: добавить phase tracking state и event handlers
3. Модифицировать `index.jsx`: добавить рендер Phase 09 компонентов
4. Добавить новые стили в `chat.css`
5. Build: `npm run build`
6. Deploy: `scp dist/chat-bundle.js aim:/var/www/.../chat/`
7. Test: пройти Testing Checklist
8. Commit: `git add AIM/theme/chat/ && git commit -m "feat: Phase 09 integration into homepage chat widget"`

**Время на реализацию:** ~2-3 часа (создание компонентов + интеграция + тестирование).

---

**Готово к утверждению. Дизайн НЕ меняется — используются существующие Tailwind классы и CSS переменные темы.**
