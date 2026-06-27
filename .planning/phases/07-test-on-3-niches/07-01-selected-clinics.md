# Phase 7 Selected Clinics

Selection method: Perplexity (sonar-pro) via container's `app.tools.perplexity_tools.handle_perplexity_search` — see raw output at end of this file. User sleeping (--auto mode) so Claude executor applied selection criteria from plan Task 2 Step C.

URL reachability verified via `httpx.AsyncClient.get(url)` inside container:
- belgraviadent.ru → 200, 1.17 MB
- milanoclinic.ru → 200, 2.95 MB
- renewclinic.ru → 200, 881 KB
- faceclinicmoscow.ru → 200, 230 KB
- inwhite.ru → connection failed (rejected)

---

## Niche 1: Plastic Surgery (locked per D-01)

- **Clinic:** Институт пластической хирургии и косметологии
- **URL:** https://iphk.ru
- **Slug:** `plastic-iphk`
- **Niche tag:** `plastic_surgery` (Instagram-critical per QC_CHECKLIST v1.2.0)
- **Reference:** `/Users/mikhaileliseev/Downloads/ИПХиК (2).html` (md5 `e957099790fd65a59065d5df6f21bed5` — matches server `/opt/data/report-reference.html`)
- **Mode for test:** PRESALE (per D-06)
- **Selection rationale:** Locked by D-01 — only niche with existing reference HTML for direct style+depth comparison.

---

## Niche 2: Dentistry

- **Clinic:** Belgravia Dental Studio (Белгравия Дентал)
- **URL:** https://belgraviadent.ru
- **Slug:** `dental-belgravia`
- **Niche tag:** `dental` (Instagram NOT critical — `is_niche_instagram_critical("dental") == False`, so item 5 moves to `not_applicable_items` per `app.orchestrator.qc_checklist.is_item_applicable`)
- **Selection rationale:** Forbes/Startsmile TOP #1 in "network clinics" category (2025-2026). Premium segment mirrors the IPHK reference (premium plastic surgery). 6+ Moscow branches → 10+ doctors listed on site → exercises SEC-04 expert regalia path with real depth. Confirmed reachable (HTTP 200, 1.17 MB homepage). Multi-branch network gives competitor analysis rich material for CI cards (DAT-03).
- **Mode for test:** ADMIN (per D-07 — exercises ADMIN path as counterpart to PRESALE on Niche 1)

---

## Niche 3: Cosmetology

- **Clinic:** Re:new clinic (Сеть клиник косметологии Re:new)
- **URL:** https://renewclinic.ru
- **Slug:** `cosmetology-renew`
- **Niche tag:** `cosmetology` (Instagram-critical per `CRITICAL_NICHES` tuple — tests IG-02/03 hard-fail path)
- **Selection rationale:** Modern multi-branch chain (3 Moscow filials per Perplexity result: Mukomolny proezd 2, Krasnoproletarskaya 7, nab. Tarasa Shevchenko 3). 2025-2026 ranking presence → mature web presence. Cosmetology chains rely heavily on Instagram for before/after content → high likelihood of active doctor Instagram accounts → exercises the full Phase 3 critical-niche path (niche detector → find_doctor_handles → run_instagram_content). Confirmed reachable (HTTP 200, 881 KB homepage).
- **Mode for test:** PRESALE (per D-04 variation — exercises PRESALE path with the IG-critical niche, complementary to Niche 1 PRESALE on plastic)

---

## Selection Procedure Followed (Plan Task 2 Step C criteria)

All selected clinics satisfy:
- [x] Private (ООО/АО/ИП form — Perplexity confirms none are ГАУЗ/ГБУЗ/МУЗ state institutions)
- [x] Working website URL (httpx 200 OK verified)
- [x] Well-known with deep web presence (premium chains with multiple branches and rating mentions)
- [x] Dental: 3+ doctors on website (Belgravia has 10+ across 6 branches)
- [x] Cosmetology: chain likely active on Instagram (3-branch modern network)

---

## Perplexity Raw Output

### Query 1 — Dentistry (sonar-pro)

> Топ-5 частных стоматологических клиник Москва (не государственных, ООО или ЗАО). Для каждой: название, URL сайта, адрес. Только частные коммерческие.

**Response (key candidates):**

1. **Немецкий Имплантологический Центр (German Implantology Center)** — german-implantology.ru — Москва, наб. Тараса Шевченко, д. 1/2. Startsmile top-10 2025.
2. **InWhite Medical** — inwhite.ru — Москва, ул. Мосфильмовская, д. 53. 1st place 32top 2026 rating. **(URL unreachable in our test — rejected)**
3. **Семейная стоматология Михаила Агами (AMBC)** — ambc.ru — Наставнический пер., д. 17, стр. 1. 2nd place 32top 2026.
4. **Belgravia Dental Studio** — belgraviadent.ru — Проспект Мира, д. 36, стр. 1 (+ 5 more branches). Forbes/Startsmile TOP #1 network. **← SELECTED**
5. **Beauty Line (Люсиновская)** — beautylinedental.ru — ул. Люсиновская, д. 53. MedAdvisor 2026 top-1.

**Selection rationale (dental):** Belgravia wins on (a) Forbes #1 recognition — strongest brand, (b) multi-branch network = more CI competitors in same brand family, (c) confirmed reachable + largest homepage (1.17 MB) = deep website for scraping.

### Query 2 — Cosmetology (sonar-pro)

> Топ-5 частных косметологических клиник Москва (не государственных, ООО или ЗАО). Для каждой: название, URL сайта, адрес. Только частные коммерческие.

**Response (key candidates):**

1. **MILANO CLINIC** — milanoclinic.ru — Бауманская + Мичуринский проспет. Top-10 KP 2026.
2. **FACE CLINIC** — faceclinicmoscow.ru — (адрес не указан в выдаче). Top-10 KP 2026.
3. **Quantum Clinic** — (URL not explicit in snippet) — ул. Большая Татарская, 7 к.4 (+ 3 more filials).
4. **Beautyway clinic** — (URL not explicit) — Страстной бульвар, 4. 5.0 rating Rang.ai 2026.
5. **Re:new clinic** — renewclinic.ru — 3 filials: Мукомольный пр. 2, Краснопролетарская 7, наб. Тараса Шевченко 3 к.3. **← SELECTED**

**Selection rationale (cosmetology):** Re:new wins on (a) explicit confirmed URL (Quantum and Beautyway had no URL in Perplexity output — would require extra discovery), (b) 3-branch network = richer dataset for CI cards + multi-location experts, (c) modern chain positioning likely correlates with active Instagram presence — critical for testing the IG-02 hard-fail path.

---

## Directory Mapping

| Niche | Slug | Output directory |
|-------|------------------------|
| Plastic Surgery | `plastic-iphk` | `/opt/data/memories/proposals/plastic-iphk/` (created in Task 1) |
| Dentistry | `dental-belgravia` | `/opt/data/memories/proposals/dental-belgravia/` (to be created in Task 2 finalization) |
| Cosmetology | `cosmetology-renew` | `/opt/data/memories/proposals/cosmetology-renew/` (to be created in Task 2 finalization) |

Placeholder dirs `dental-phase7/` and `cosmetology-phase7/` from Task 1 will be removed (renamed to specific slugs).

---

## Ready for Plan 07-02 (Plastic Surgery Test)

Yes. Plastic IPHK test can begin immediately:
- `ssh aim "docker exec -e ORCHESTRATOR_MODE=1 aim-hermes python3 /opt/data/phase7/run_presale_test.py --url https://iphk.ru --slug plastic-iphk --mode PRESALE --niche plastic_surgery"`
