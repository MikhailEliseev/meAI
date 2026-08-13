"""Аудит: какие инструменты РЕАЛЬНО отдают данные на 11 клиниках."""
import json, os

bases = ["/opt/hermes-v2-data/golden_all", "/opt/hermes-v2-data/golden_new5",
         "/opt/hermes-v2-data/golden_lazy", "/opt/hermes-v2-data/golden_recs4"]
all_snaps = {}
for base in bases:
    if not os.path.exists(base): continue
    for cid in os.listdir(base):
        p = os.path.join(base, cid, "snapshot.json")
        if os.path.exists(p) and cid not in all_snaps:
            all_snaps[cid] = json.load(open(p))

print(f"=== Анализ {len(all_snaps)} клиник ===\n")

tool_stats = {}
for cid, s in all_snaps.items():
    seen_tools = set()
    for tc in s["events"].get("tool_calls", []):
        name = tc.get("tool", "")
        result = str(tc.get("result", ""))
        has_data = len(result) > 30 and "error" not in result.lower()[:60]
        # считаем 1 раз на клинику
        if name not in seen_tools:
            seen_tools.add(name)
            st = tool_stats.setdefault(name, {"clinics": 0, "with_data": 0})
            st["clinics"] += 1
            if has_data: st["with_data"] += 1

print("ИНСТРУМЕНТ                        клиник  с данными  %")
print("-" * 55)
for name in sorted(tool_stats, key=lambda x: tool_stats[x]["clinics"], reverse=True):
    st = tool_stats[name]
    pct = round(st["with_data"] / st["clinics"] * 100) if st["clinics"] else 0
    flag = " ✅" if pct >= 70 else (" ⚠️" if pct >= 30 else " ❌")
    print(f"  {name:30}  {st['clinics']:4}     {st['with_data']:4}     {pct:3}%{flag}")

# Детально: какие поля реально заполнены
print("\n=== КАКИЕ ПОЛЯ РЕАЛЬНО ЗАПОЛНЕНЫ (по find_competitors) ===")
field_fill = {}
for cid, s in all_snaps.items():
    for tc in s["events"]["tool_calls"]:
        if tc.get("tool") == "find_competitors":
            r = json.loads(tc["result"]) if isinstance(tc["result"], str) else tc["result"]
            for k in ["client_revenue", "client_profit", "client_inn"]:
                v = r.get(k)
                ff = field_fill.setdefault(k, {"filled": 0, "total": 0})
                ff["total"] += 1
                if v: ff["filled"] += 1
            for c in r.get("competitors", []):
                for k in ["revenue_year", "profit_year", "doctors_count", "instagram_followers", "revenue_trend"]:
                    v = c.get(k)
                    ff = field_fill.setdefault("comp." + k, {"filled": 0, "total": 0})
                    ff["total"] += 1
                    if v: ff["filled"] += 1
            break

for k, ff in sorted(field_fill.items()):
    pct = round(ff["filled"] / ff["total"] * 100) if ff["total"] else 0
    flag = " ✅" if pct >= 70 else (" ⚠️" if pct >= 30 else " ❌")
    print(f"  {k:30} {ff['filled']:3}/{ff['total']:3} ({pct:3}%){flag}")

print("\n=== КАКИЕ ПОЛЯ В REVIEWS ===")
rev_fill = {}
for cid, s in all_snaps.items():
    for tc in s["events"]["tool_calls"]:
        if tc.get("tool") == "run_review_platforms":
            r = json.loads(tc["result"]) if isinstance(tc["result"], str) else tc["result"]
            plats = r.get("platforms", {})
            for pname, pdata in plats.items() if isinstance(plats, dict) else []:
                if not isinstance(pdata, dict) or not pdata: continue
                for k in ["rating", "reviews"]:
                    v = pdata.get(k)
                    ff = rev_fill.setdefault(f"{pname}.{k}", {"filled": 0, "total": 0})
                    ff["total"] += 1
                    if v: ff["filled"] += 1
            break

for k, ff in sorted(rev_fill.items()):
    pct = round(ff["filled"] / ff["total"] * 100) if ff["total"] else 0
    flag = " ✅" if pct >= 70 else (" ⚠️" if pct >= 30 else " ❌")
    print(f"  {k:30} {ff['filled']:3}/{ff['total']:3} ({pct:3}%){flag}")
