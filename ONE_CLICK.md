# 🎯 ONE-CLICK ARCHITECT

**Самый простой способ общаться с Architect!**

---

## 🚀 Использование

### Вариант 1: Одна команда

```bash
./architect.sh "Твой вопрос"
```

**Примеры:**

```bash
./architect.sh "Какую нишу выбрать первой?"
./architect.sh "Создай SEO агента для стоматологии"
./architect.sh "Запусти создание AIM Agency"
./architect.sh "Какую цену ставить на SEO-аудит?"
```

---

### Вариант 2: Интерактивный режим

Просто запусти без параметров:

```bash
./architect.sh
```

Увидишь инструкцию и примеры.

---

## 📋 Что происходит

```
ТЫ
  ↓ ./architect.sh "вопрос"
СКРИПТ
  ↓ активирует venv
  ↓ запускает Architect CLI
ARCHITECT
  ↓ анализирует
  ↓ возвращает решение
ТЫ
  ↓ видишь результат
```

---

## ✅ Преимущества

- ✅ **Один клик** — просто запусти скрипт
- ✅ **Автоматически** активирует venv
- ✅ **Красивый вывод** с цветами
- ✅ **Примеры** встроены
- ✅ **Быстро** — без лишних действий

---

## 📁 Где результаты

Все решения сохраняются в:

```
obsidian/architect/decisions/YYYYMMDD-HHMM-decision.md
```

---

## 🎯 Быстрый старт

**Шаг 1:** Открой терминал

**Шаг 2:** Перейди в проект

```bash
cd /Users/mikhaileliseev/Desktop/Dev/!meAI
```

**Шаг 3:** Запусти

```bash
./architect.sh "Какую первую задачу дать AIM Agency?"
```

**Готово!** 🎉

---

## 💡 Альтернативы

Если хочешь использовать другие интерфейсы:

### В Claude Code (этот чат):
```
/architect Какую нишу выбрать?
```

### Через Telegram Bot:
```bash
./start_bot.sh
# Потом пиши в Telegram
```

---

## 🔧 Troubleshooting

**Ошибка: "Permission denied"**
```bash
chmod +x architect.sh
```

**Ошибка: "venv not found"**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Ошибка: "ANTHROPIC_API_KEY not found"**
```bash
# Проверь .env файл
cat .env
```

---

**Готово! Теперь у тебя есть ONE-CLICK доступ к Architect! 🚀**
