# 🎯 Quick Start: Общение с Architect

**Последнее обновление:** 2026-05-03 19:23 GMT+3

---

## 🚀 НОВОЕ! Через Claude Code (Самый простой способ)

Просто напиши в этом чате:

```
/architect Какую первую задачу дать AIM Agency?
```

**Примеры:**

```
/architect Какую нишу выбрать первой?
/architect Создай SEO агента для стоматологии
/architect Запусти создание AIM Agency
/architect Какую цену ставить на SEO-аудит?
```

**Что произойдёт:**
1. Architect получит вопрос
2. Проанализирует через Claude API
3. Вернёт решение с планом
4. Спросит: "Реализовать?"
5. Если да → Claude Code реализует план
6. Результат сохранится в Obsidian

📖 **Подробнее:** `ARCHITECT_USAGE.md`

---

## 1. Через CLI (Терминал)

```bash
source venv/bin/activate
python scripts/talk_to_architect.py "Твой вопрос"
```

**Пример:**
```bash
python scripts/talk_to_architect.py "Какую нишу выбрать первой?"
```

---

## 2. Через Telegram Bot (Рекомендуется 👍)

### Первый запуск:

**Шаг 1: Создай бота**
1. Открой [@BotFather](https://t.me/botfather) в Telegram
2. Отправь `/newbot`
3. Введи имя: `AIM Architect`
4. Введи username: `aim_architect_bot` (или любой свободный)
5. Скопируй токен

**Шаг 2: Настрой переменные**
```bash
export TELEGRAM_BOT_TOKEN="твой_токен_от_BotFather"
export ASSEMBLYAI_API_KEY="твой_ключ_от_AssemblyAI"
```

**Шаг 3: Запусти бота**
```bash
source venv/bin/activate
python scripts/telegram_bot.py
```

**Шаг 4: Открой бота в Telegram**
1. Найди своего бота по username
2. Нажми `/start`
3. Начни общаться!

### Использование:

**Текстом:**
```
Какую цену ставить на SEO-аудит?
```

**Голосом:**
1. Нажми микрофон
2. Надиктуй вопрос
3. Отправь
4. Бот расшифрует и ответит

**Команды:**
- `/start` - инструкция
- `/help` - справка
- `/history` - последние решения

---

## Примеры вопросов

**Стратегия:**
- Какую нишу выбрать первой: стоматология или косметология?
- С чего начать запуск агентства?
- Нужен ли партнёр-разработчик?

**Продукт:**
- Какой первый агент запустить: SEO или Content?
- Какие функции включить в MVP?

**Ценообразование:**
- Какую цену ставить на SEO-аудит через AI?
- Как упаковать услуги?

**Маркетинг:**
- Как найти первых клиентов?
- Какой канал продаж использовать?

---

## Где хранятся решения?

Все решения автоматически сохраняются в:
```
obsidian/architect/decisions/YYYYMMDD-HHMM-decision.md
```

Можешь открыть в Obsidian и посмотреть полную историю.

---

## Troubleshooting

**Бот не отвечает:**
```bash
# Проверь токен
echo $TELEGRAM_BOT_TOKEN

# Перезапусти бота
python scripts/telegram_bot.py
```

**Ошибка транскрипции:**
```bash
# Проверь API ключ AssemblyAI
echo $ASSEMBLYAI_API_KEY
```

**Ошибка Architect:**
```bash
# Проверь, что Claude работает
python scripts/talk_to_architect.py "test"
```

---

## Запуск в фоне

Чтобы бот работал постоянно:

```bash
# С nohup
nohup python scripts/telegram_bot.py > telegram_bot.log 2>&1 &

# Или с screen
screen -S architect_bot
python scripts/telegram_bot.py
# Ctrl+A, D для detach
```

---

**Готово! Теперь можешь общаться с Architect откуда угодно!** 🚀
