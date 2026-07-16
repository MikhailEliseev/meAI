# HH API Authorization

## Проблема

HH API требует OAuth2 авторизацию для доступа к вакансиям и резюме.

**Текущий статус:** 403 Forbidden при попытке доступа к `/vacancies`

## Что работает без авторизации

- `/dictionaries` - справочники
- `/areas` - регионы
- `/industries` - индустрии
- `/professional_roles` - профессиональные роли
- `/languages` - языки
- `/skills` - навыки

## Что требует авторизации

- `/vacancies` - поиск вакансий ❌
- `/resumes` - поиск резюме ❌
- `/employers/{id}` - информация о работодателе ❌
- `/negotiations` - отклики/приглашения ❌

## Решение

### Вариант 1: OAuth Application Token (рекомендуется)

1. Зарегистрировать приложение на https://dev.hh.ru
2. Получить `client_id` и `client_secret`
3. Запросить application token:

```bash
curl -X POST https://api.hh.ru/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

4. Использовать токен в заголовке:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "HH-User-Agent: AIM-CI-Agent/1.0 (me@mikhaileliseev.com)" \
     https://api.hh.ru/vacancies?employer_id=1740
```

### Вариант 2: Web Scraping (альтернатива)

Если OAuth недоступен, можно парсить публичные страницы hh.ru:
- `https://hh.ru/employer/{employer_id}`
- `https://hh.ru/search/vacancy?employer_id={employer_id}`

**Минусы:**
- Нестабильно (изменения в HTML)
- Медленнее
- Может быть заблокировано

### Вариант 3: Playwright + Browser Automation

Использовать Playwright для автоматизации браузера:
- Авторизация через UI
- Сбор данных через DOM
- Обход rate limits

## Следующие шаги

1. ✅ Создать структуру HH Agent
2. ✅ Реализовать базовый функционал
3. ⏳ Зарегистрировать приложение на dev.hh.ru
4. ⏳ Получить OAuth токен
5. ⏳ Обновить агента для работы с токеном

## Временное решение

Пока OAuth не настроен, можно:
- Использовать mock данные для тестирования
- Парсить публичные страницы
- Использовать Playwright для автоматизации

---

**Дата:** 2026-05-04
**Статус:** Требуется OAuth токен
