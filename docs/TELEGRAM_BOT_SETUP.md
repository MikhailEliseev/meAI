# Telegram Bot Setup

Инструкция по настройке Telegram бота для общения с Architect.

## Шаг 1: Создать бота в Telegram

1. Открой Telegram и найди [@BotFather](https://t.me/botfather)
2. Отправь команду `/newbot`
3. Введи имя бота (например: `AIM Architect`)
4. Введи username бота (например: `aim_architect_bot`)
5. Получишь токен вида: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

## Шаг 2: Получить API ключ AssemblyAI

У тебя уже есть аккаунт на AssemblyAI:

1. Зайди на [AssemblyAI Dashboard](https://www.assemblyai.com/app)
2. Скопируй API Key

## Шаг 3: Установить зависимости

```bash
source venv/bin/activate
pip install python-telegram-bot assemblyai
```

## Шаг 4: Настроить переменные окружения

Добавь в `.env` или экспортируй:

```bash
export TELEGRAM_BOT_TOKEN="твой_токен_от_BotFather"
export ASSEMBLYAI_API_KEY="твой_ключ_от_AssemblyAI"
```

Или создай файл `.env`:

```bash
cat > .env << EOF
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ASSEMBLYAI_API_KEY=твой_ключ
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
EOF
```

## Шаг 5: Запустить бота

```bash
source venv/bin/activate
python scripts/telegram_bot.py
```

Бот запустится и будет ждать сообщений.

## Использование

### Текстовые сообщения

Просто напиши вопрос:
```
Какую нишу выбрать первой: стоматология или косметология?
```

### Голосовые сообщения

1. Нажми на микрофон в Telegram
2. Надиктуй вопрос
3. Отправь
4. Бот расшифрует и ответит

### Команды

- `/start` - показать инструкцию
- `/help` - показать справку
- `/history` - последние 5 решений

## Примеры вопросов

**Стратегия:**
- Какую нишу выбрать первой?
- С чего начать запуск агентства?
- Нужен ли партнёр-разработчик?

**Продукт:**
- Какой первый агент запустить: SEO или Content?
- Какие функции включить в MVP?
- Как приоритизировать фичи?

**Ценообразование:**
- Какую цену ставить на SEO-аудит?
- Как упаковать услуги?
- Какую модель монетизации выбрать?

**Маркетинг:**
- Как найти первых клиентов?
- Какой канал продаж использовать?
- Как позиционировать AI-first подход?

## Troubleshooting

### Бот не отвечает

Проверь:
```bash
# Токен установлен?
echo $TELEGRAM_BOT_TOKEN

# Бот запущен?
ps aux | grep telegram_bot
```

### Ошибка транскрипции

Проверь:
```bash
# API ключ установлен?
echo $ASSEMBLYAI_API_KEY

# Квота не закончилась?
# Зайди на https://www.assemblyai.com/app
```

### Ошибка Architect

Проверь:
```bash
# Claude работает?
python scripts/talk_to_architect.py "test"
```

## Остановка бота

```bash
# Ctrl+C в терминале
# Или найди процесс и убей:
ps aux | grep telegram_bot
kill <PID>
```

## Запуск в фоне

```bash
# С nohup
nohup python scripts/telegram_bot.py > telegram_bot.log 2>&1 &

# Или с screen
screen -S architect_bot
python scripts/telegram_bot.py
# Ctrl+A, D для detach
```

## Безопасность

⚠️ **Важно:**
- Не коммить `.env` в git
- Не делиться токеном бота
- Не публиковать API ключи
- Добавить `.env` в `.gitignore`

## Что дальше?

После настройки бота ты можешь:
- Общаться с Architect из любого места
- Диктовать вопросы голосом
- Получать стратегические решения в Telegram
- Все решения сохраняются в Obsidian

Удачи! 🚀
