# Linear Integration

## Overview

Linear CLI integration для управления задачами проекта meAI через командную строку.

## Setup

API ключ уже настроен в `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@mseep/linear-mcp"],
      "env": {
        "LINEAR_API_KEY": "YOUR_LINEAR_API_KEY_HERE"
      }
    }
  }
}
```

## Usage

### Wrapper Script (Recommended)

Используй `scripts/linear` wrapper для автоматической подстановки API ключа:

```bash
# Список всех задач
scripts/linear list

# Детали задачи
scripts/linear show MIK-5

# Создать задачу
scripts/linear create "Task Title" "Task Description" --priority 2

# Обновить статус
scripts/linear update MIK-5 --state "In Progress"

# Добавить комментарий
scripts/linear comment MIK-5 "Comment text"

# Список команд
scripts/linear teams

# Список статусов
scripts/linear states <team-id>
```

### Direct CLI

Или используй `linear_cli.py` напрямую с API ключом:

```bash
LINEAR_API_KEY="..." python3 scripts/linear_cli.py list
```

## Available Commands

### list
Список всех задач:
```bash
scripts/linear list [--limit 50]
```

### show
Детали задачи:
```bash
scripts/linear show MIK-1
```

### create
Создать новую задачу:
```bash
scripts/linear create "Title" "Description" [--priority 0-4]
```

### update
Обновить задачу:
```bash
scripts/linear update MIK-1 [--title "New Title"] [--description "New Desc"] [--state "In Progress"] [--priority 2]
```

### comment
Добавить комментарий:
```bash
scripts/linear comment MIK-1 "Comment text"
```

### teams
Список команд:
```bash
scripts/linear teams
```

### states
Список workflow статусов:
```bash
scripts/linear states <team-id>
```

## Workflow States

Доступные статусы для команды Mikhaileliseev:

- **Backlog** (backlog) - Задачи в бэклоге
- **Todo** (unstarted) - Готово к работе
- **In Progress** (started) - В работе
- **In Review** (started) - На ревью
- **Done** (completed) - Завершено
- **Canceled** (canceled) - Отменено
- **Duplicate** (canceled) - Дубликат

## Priority Levels

- **0** - No priority
- **1** - Urgent
- **2** - High
- **3** - Medium
- **4** - Low

## Examples

### Создать задачу для meAI проекта

```bash
scripts/linear create "Implement SEO Agent" "Create SEO agent with keyword research and competitor analysis" --priority 2
```

### Перевести задачу в работу

```bash
scripts/linear update MIK-5 --state "In Progress"
```

### Добавить прогресс

```bash
scripts/linear comment MIK-5 "Completed keyword research API integration"
```

### Завершить задачу

```bash
scripts/linear update MIK-5 --state "Done"
```

## Integration with meAI

Linear CLI интегрирован с проектом meAI для:

1. **Task Tracking** - Отслеживание задач разработки
2. **Progress Updates** - Обновление прогресса через CLI
3. **Team Coordination** - Координация работы команды
4. **Automation** - Автоматизация создания задач из кода

## API Reference

Linear GraphQL API: https://developers.linear.app/docs/graphql/working-with-the-graphql-api

## Troubleshooting

### API Key Not Found

Если получаешь ошибку "LINEAR_API_KEY not found":

1. Проверь `~/.claude/settings.json`
2. Убедись, что секция `mcpServers.linear.env.LINEAR_API_KEY` существует
3. Перезапусти Claude Code

### Connection Issues

Если не можешь подключиться к Linear API:

1. Проверь интернет соединение
2. Проверь валидность API ключа на https://linear.app/settings/api
3. Проверь, что API ключ имеет нужные права (read/write issues)

## Next Steps

1. ✅ Linear CLI integration работает
2. ⏳ Создать задачи для текущего спринта
3. ⏳ Интегрировать с meAI Operator для автоматического создания задач
4. ⏳ Добавить синхронизацию между Linear и Obsidian vaults
