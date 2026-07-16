---
name: record-all-keys
description: Always save API keys, credentials, and configuration values the user shares
metadata:
  type: feedback
---

**Правило:** Когда пользователь даёт API-ключ, пароль, токен или любые другие учётные данные — ОБЯЗАТЕЛЬНО записывать их:
1. В `.env.production` на сервере (если production)
2. В локальный `.env` и `.env.example` (для документации)
3. В память — какой ключ и куда сохранён

**Why:** Пользователь дал Brave API Key ранее в разговоре, я не записал его никуда. Он потерял время и разозлился. Повторять нельзя.

**How to apply:** Когда пользователь даёт credentials любого рода — немедленно сохранить в соответствующие файлы, не ждать отдельной команды.
