# Phase 7 Pre-flight Scout Report

Date: 2026-06-24 (autonomous, --auto mode)
Container: aim-hermes
Server: AIM-Server-PL (78.17.128.169, root@AIM-Server-PL)

## Check Results

| # | Check | Expected | Actual | Status |
|---|-------|----------|--------|--------|
| 1 | Container health | Up, healthy | Up 46 hours, healthy | PASS |
| 2 | Tool handlers count | 26 | 26 | PASS |
| 3 | QC checklist version | 18 items, 1.2.0 | 18 1.2.0 | PASS |
| 4 | Orchestrator imports | OK | OK | PASS |
| 5a | Reference HTML md5 (server) | e957099790fd65a59065d5df6f21bed5 | e957099790fd65a59065d5df6f21bed5 | PASS |
| 5b | Reference HTML md5 (local)  | e957099790fd65a59065d5df6f21bed5 | e957099790fd65a59065d59065d5df6f21bed5 (md5 cmd output) | PASS |
| 6 | Proposals directory exists | drwxr-xr-x | drwxr-xr-x 6 1000 1000 (4 subdirs) | PASS |
| 7 | Phase 7 test directory created | /opt/data/phase7 exists | drwxr-xr-x 2 root root 4096 Jun 24 05:31 | PASS |
| 8 | Output directories for 3 niches | plastic-iphk, dental-phase7, cosmetology-phase7 created | All 3 present (plus pre-existing arclinic) | PASS |

## Raw Command Outputs

### Check 1 — Container health
```
$ ssh aim "docker ps --format '{{.Names}}\t{{.Status}}' | grep aim-hermes"
aim-hermes	Up 46 hours (healthy)
```

### Check 2 — Tool handlers count
```
$ ssh aim "docker exec aim-hermes python3 -c '...'"
26
```

### Check 3 — QC checklist version
```
$ ssh aim "docker exec aim-hermes python3 -c '...'"
18 1.2.0
```

### Check 4 — Orchestrator imports clean
```
$ ssh aim "docker exec aim-hermes python3 -c '...'"
OK
```

### Check 5a — Reference HTML md5 (server, inside container)
```
$ ssh aim "docker exec aim-hermes md5sum /opt/data/report-reference.html"
e957099790fd65a59065d5df6f21bed5  /opt/data/report-reference.html
```

### Check 5b — Reference HTML md5 (local)
```
$ md5 "/Users/mikhaileliseev/Downloads/ИПХиК (2).html"
MD5 (/Users/mikhaileliseev/Downloads/ИПХиК (2).html) = e957099790fd65a59065d5df6f21bed5
```

### Check 6 — Proposals directory exists
```
$ ssh aim "docker exec aim-hermes ls -ld /opt/data/memories/proposals/"
drwxr-xr-x 6 1000 1000 4096 Jun 24 05:31 /opt/data/memories/proposals/
```

### Check 7 — Phase 7 test directory created
```
$ ssh aim "docker exec aim-hermes mkdir -p /opt/data/phase7"
$ ssh aim "docker exec aim-hermes ls -ld /opt/data/phase7"
drwxr-xr-x 2 root root 4096 Jun 24 05:31 /opt/data/phase7
```

### Check 8 — Output directories for 3 niches created
```
$ ssh aim "docker exec aim-hermes mkdir -p /opt/data/memories/proposals/plastic-iphk /opt/data/memories/proposals/dental-phase7 /opt/data/memories/proposals/cosmetology-phase7"
$ ssh aim "docker exec aim-hermes ls /opt/data/memories/proposals/"
arclinic
cosmetology-phase7
dental-phase7
plastic-iphk
```

## Container Configuration Confirmed

- TOOL_HANDLERS: 26 entries
- QC_CHECKLIST: 18 items v1.2.0
- ORCHESTRATOR_MODE: unset (will be injected per-test via `docker exec -e ORCHESTRATOR_MODE=1`)
- Reference HTML md5: `e957099790fd65a59065d5df6f21bed5` (server `/opt/data/report-reference.html` matches local `/Users/mikhaileliseev/Downloads/ИПХиК (2).html`)
- Container: Up 46 hours, healthy
- Existing pre-existing subdirectory `arclinic/` (empty) preserved — no clobber
- `/opt/data/phase7/` directory ready for test harness deployment
- `/opt/data/run_phase0_iphk.py` and `/opt/data/run_phase1_iphk.py` untouched (referenced as example patterns only)

## Blockers

None.

## Deviations

**[Rule 3 — blocking issue]** Initial invocation of Check 7 used a shell construct of the form `ssh aim "docker exec aim-hermes mkdir -p X && ls -ld X"`. The `&&` was parsed by the remote HOST shell, not the container shell — so `mkdir` ran inside the container (succeeded) but `ls` ran on the host server (`/opt/data/phase7` does not exist on host → exit 2). Fix: split commands into separate `ssh aim "docker exec ..."` invocations OR wrap the whole chain in `sh -c '...'` inside the container. No semantic impact — directories were created correctly on the first invocation; only the verification `ls` was misdirected. Same root cause for Check 8.

## Ready for Task 2

Yes.
