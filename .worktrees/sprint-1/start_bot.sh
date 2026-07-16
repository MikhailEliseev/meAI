#!/bin/bash

# Запуск Telegram бота для Architect

echo "🚀 Запуск Architect Telegram Bot..."
echo ""

# Активируем venv
source venv/bin/activate

# Устанавливаем переменные окружения
export TELEGRAM_BOT_TOKEN="8797921353:AAE5s_-XVwx98S_V81aMnW7Io0MTjlyCWZc"
export ASSEMBLYAI_API_KEY="e2ccb519aea0475fbe1dc3183deedc51"

echo "✅ Переменные окружения установлены"
echo "✅ Bot username: @aimarchitector_bot"
echo ""
echo "Запускаю бота..."
echo "Нажми Ctrl+C для остановки"
echo ""

# Запускаем бота
python scripts/telegram_bot.py
