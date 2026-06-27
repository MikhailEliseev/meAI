# Phase 27: Presale Conveyor — JSON Contract + State Machine + Quality Gate

**Status:** Planned
**Goal:** Превратить 7 скиллов в конвейер: единый формат данных, structured state, программный quality gate.

## Tasks

### Task 1: PresaleData JSON schema
**Type:** create
**Target:** `/root/.hermes/skills/software-development/presale-pipeline/schemas/presale-data.schema.json`

Создать JSON Schema для `data.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PresaleData",
  "type": "object",
  "required": ["meta", "clinic", "doctors", "competitors", "content", "geo"],
  "properties": {
    "meta": {
      "type": "object",
      "required": ["client", "url", "generated_at"],
      "properties": {
        "client": {"type": "string"},
        "url": {"type": "string", "format": "uri"},
        "generated_at": {"type": "string", "format": "date-time"}
      }
    },
    "clinic": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "inn": {"type": "string"},
        "revenue": {"type": "number"},
        "profit": {"type": "number"},
        "employees": {"type": "integer"},
        "tech_audit": {
          "type": "object",
          "properties": {
            "speed_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "broken_links": {"type": "integer"},
            "meta_ok": {"type": "boolean"},
            "h1_ok": {"type": "boolean"},
            "alt_ok": {"type": "boolean"},
            "sitemap_ok": {"type": "boolean"},
            "ssl_ok": {"type": "boolean"},
            "mobile_ok": {"type": "boolean"}
          }
        }
      }
    },
    "doctors": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["full_name"],
        "properties": {
          "full_name": {"type": "string"},
          "specialty": {"type": "string"},
          "ig_username": {"type": "string"},
          "ig_followers": {"type": "integer"},
          "ig_verified": {"type": "boolean"},
          "tg_username": {"type": "string"},
          "vk_url": {"type": "string"},
          "pass_found": {"type": "integer", "minimum": 0, "maximum": 5},
          "confidence": {"type": "string", "enum": ["verified", "single-source", "estimated"]}
        }
      }
    },
    "competitors": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": {"type": "string"},
          "url": {"type": "string"},
          "revenue": {"type": "number"},
          "profit": {"type": "number"},
          "score": {"type": "number", "minimum": 0, "maximum": 100},
          "strengths": {"type": "array", "items": {"type": "string"}},
          "viral_posts": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "content": {
      "type": "object",
      "properties": {
        "winning_formats": {"type": "array", "items": {"type": "string"}},
        "white_space": {"type": "array", "items": {"type": "string"}},
        "expert_cards": {"type": "array"}
      }
    },
    "geo": {
      "type": "object",
      "properties": {
        "schema_ok": {"type": "boolean"},
        "chatgpt_geo": {"type": "boolean"},
        "yandex_maps": {"type": "boolean"},
        "google_maps": {"type": "boolean"},
        "local_seo_score": {"type": "integer", "minimum": 0, "maximum": 100}
      }
    }
  }
}
```

**Verify:** `python3 -c "import json; json.load(open('schemas/presale-data.schema.json')); print('Valid JSON Schema')"`

### Task 2: State machine spec + template
**Type:** create
**Target:** `/root/work/presale/presale-state.template.json`

Создать шаблон state machine и документацию:

```json
{
  "client": "",
  "url": "",
  "phase": 0,
  "step": "init",
  "completed": [],
  "pending": [
    "phase0-site-audit",
    "phase0-finance",
    "phase1-social-audit",
    "phase1-competitors",
    "phase1-reels",
    "phase2-content-analysis",
    "phase2-gap-audit",
    "phase4-html-kp"
  ],
  "errors": [],
  "gaps": 0,
  "iterations": 0,
  "started_at": "",
  "updated_at": ""
}
```

Правила обновления state machine прописать в parent SKILL.md:
- После каждого tool-вызова → обновить `updated_at` + сдвинуть step
- При ошибке → добавить в `errors[]`
- При завершении фазы → перенести из `pending[]` в `completed[]`

### Task 3: quality-gate.py
**Type:** create
**Target:** `/root/bin/quality-gate.py`

```python
#!/usr/bin/env python3
"""Quality Gate — блокирует HTML при наличии gaps."""
import json
import sys
from pathlib import Path

def validate_presale(data_path: str) -> tuple[bool, list[str]]:
    """Проверяет data.json на полноту."""
    data = json.loads(Path(data_path).read_text())
    gaps = []

    # 1. Clinic check
    if not data.get("clinic", {}).get("inn"):
        gaps.append("MISSING: clinic.inn")
    if not data.get("clinic", {}).get("revenue"):
        gaps.append("MISSING: clinic.revenue")
    if not data.get("clinic", {}).get("tech_audit"):
        gaps.append("MISSING: clinic.tech_audit")

    # 2. Doctors check
    doctors = data.get("doctors", [])
    if not doctors:
        gaps.append("MISSING: doctors (empty)")
    for i, doc in enumerate(doctors):
        if not doc.get("ig_username"):
            gaps.append(f"MISSING: doctors[{i}].ig_username ({doc.get('full_name', '?')})")
        if doc.get("confidence") != "verified":
            gaps.append(f"LOW_CONFIDENCE: doctors[{i}] ({doc.get('full_name', '?')}) = {doc.get('confidence')}")

    # 3. Competitors check
    competitors = data.get("competitors", [])
    if not competitors:
        gaps.append("MISSING: competitors (empty)")
    for i, comp in enumerate(competitors):
        if not comp.get("revenue"):
            gaps.append(f"MISSING: competitors[{i}].revenue ({comp.get('name', '?')})")
        if not comp.get("score"):
            gaps.append(f"MISSING: competitors[{i}].score ({comp.get('name', '?')})")

    # 4. GEO check
    geo = data.get("geo", {})
    if not geo:
        gaps.append("MISSING: geo (empty)")
    for key in ["schema_ok", "chatgpt_geo", "yandex_maps", "google_maps"]:
        if key not in geo:
            gaps.append(f"MISSING: geo.{key}")

    return (len(gaps) == 0, gaps)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: quality-gate.py <data.json>")
        sys.exit(2)

    passed, gaps = validate_presale(sys.argv[1])

    if passed:
        print("✅ QUALITY GATE: PASSED — 0 gaps")
        sys.exit(0)
    else:
        print(f"🚫 QUALITY GATE: FAILED — {len(gaps)} gaps:")
        for g in gaps:
            print(f"  - {g}")
        sys.exit(1)
```

**Verify:** `python3 /root/bin/quality-gate.py --help` (или ручной запуск с тестовым data.json)

### Task 4: Обновить html-kp-generator — читать data.json
**Type:** modify
**Target:** `/root/.hermes/skills/software-development/html-kp-generator/SKILL.md`

Добавить в metadata и workflow:
```yaml
input_schema: schemas/presale-data.schema.json
input_format: JSON
input_path: /root/work/presale/{client}/data.json
```

В workflow первым шагом: «Прочитай `/root/work/presale/{client}/data.json` — все 12 блоков HTML строятся только из этого файла.»

### Task 5: Обновить parent SKILL.md — state machine + quality gate
**Type:** modify
**Target:** `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md`

Добавить в Phase 0 инициализацию state machine:
- Копировать `presale-state.template.json` → `/root/work/presale/{client}/presale-state.json`
- Заполнить `client`, `url`, `started_at`

Добавить в Phase 4 вызов quality gate:
- Перед html-kp-generator: `python3 /root/bin/quality-gate.py /root/work/presale/{client}/data.json`
- Если exit code ≠ 0 → не генерировать HTML, вернуться к Goal Loop

### Task 6: Verify — test quality gate on sample data
**Type:** verify
**Target:** server

Создать тестовый `data.json` с пропущенными полями и проверить, что quality-gate.py возвращает FAIL. Затем заполнить все поля и проверить PASS.

## Files

### Create (4):
1. `/root/.hermes/skills/software-development/presale-pipeline/schemas/presale-data.schema.json`
2. `/root/work/presale/presale-state.template.json`
3. `/root/bin/quality-gate.py`
4. `/root/work/presale/presale-state.template.json`

### Modify (2):
5. `/root/.hermes/skills/software-development/html-kp-generator/SKILL.md` — добавить input JSON
6. `/root/.hermes/skills/software-development/presale-pipeline/SKILL.md` — state machine + quality gate интеграция

## Verification
1. `python3 -c "import json; json.load(open('schemas/presale-data.schema.json'))"` — schema валидна
2. `python3 /root/bin/quality-gate.py /root/work/presale/test-empty.json` → FAIL
3. `python3 /root/bin/quality-gate.py /root/work/presale/test-complete.json` → PASS
4. html-kp-generator читает data.json
5. Parent SKILL.md содержит state machine init + quality gate вызов
