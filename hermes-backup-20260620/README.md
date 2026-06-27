# Hermes Backup — 2026-06-20

## Состав

| Файл | Размер | Содержимое |
|------|--------|-----------|
| `hermes-20260620-code.tar.gz` | 398 KB | Код, конфиг, скиллы |
| `hermes-20260620-image.tar.gz` | ~780 MB | Docker образ aim-hermes:latest |

## Что внутри code-бекапа
- `app/pipeline/` — 13 фаз + mode_gate + file_guard + engine (1505 строк)
- `app/tools/` — 53 инструмента включая scrapy_runner
- `app/key_bank.py` — реестр API-ключей (450 строк)
- `app/agent_wrapper.py` + `agent_wrapper_optimized.py`
- `config.yaml` — конфиг Hermes
- `skills/` — 5 скиллов
- `MANIFEST.txt` — последние 10 коммитов

## Восстановление

```bash
# 1. Восстановить код
cd /opt/aim/AIM/
tar -xzf hermes-20260620-code.tar.gz

# 2. Восстановить Docker образ
docker load < hermes-20260620-image.tar.gz

# 3. Перезапустить
cd /opt/aim/AIM && docker compose up -d hermes
```

## Состояние на момент бекапа
- PRESALE: 13 инструментов (run_full_scout + CRM)
- ADMIN: 39 инструментов
- Key Bank: 11/23 active
- Git: main @ 7bf8971
