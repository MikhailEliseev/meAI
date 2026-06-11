# Session: 2026-06-11

## Текущий фокус: Перестройка iamaim.ru — выполняю план (14 tasks)

### Статус
- ✅ Task 1: CPT `research` зарегистрирован (sandbox auto-loader)
- ✅ Task 2: Старые страницы удалены, Contact создан, permalinks настроены
- ✅ Task 3: style.css (217 B)
- ✅ Task 4: functions.php (3.4 KB) — theme setup, enqueue, REST proxy, settings page
- ✅ Task 5: header.php (1.1 KB) + footer.php (981 B)
- ✅ Task 6: index.php (374 B)
- ✅ Task 7: theme.css (4.7 KB, Tailwind скомпилирован)
- ✅ Task 8: animated-text.js (819 B)
- ⏳ Task 9: React chat bundle (следующий)
- ⏳ Tasks 10-14: front-page, research, blog/contact, activation, SEO

### Важные выводы
- **MCP write-file НЕНАДЁЖЕН для PHP копирования в тему.** Писать PHP напрямую в Docker volume: `/var/lib/docker/volumes/aim_wp_content/_data/themes/aim-theme/`
- **MCP execute-php может писать в sandbox**, но копирование из sandbox в тему работало нестабильно
- **Sandbox auto-loader:** если PHP-файл в sandbox вызывает фатальную ошибку → `.crashed` → safe mode → MCP недоступен
- **CSS/JS пишутся напрямую** в Docker volume — это работало стабильно
- WordPress контейнер: `aim-wp`, wp-content смонтирован как Docker volume `aim_wp_content`
