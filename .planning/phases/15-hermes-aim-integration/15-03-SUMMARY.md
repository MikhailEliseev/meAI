---
phase: 15-hermes-aim-integration
plan: 03
subsystem: fastapi-http-wrapper
tags: [hermes, fastapi, docker, nextjs, chat-proxy, retry, redis-fallback]

# Dependency graph
requires: [15-01-operator-identity, 15-02-aim-tools]
provides:
  - "Dockerfile for Hermes container (Python 3.11, hermes-agent v0.14.0)"
  - "FastAPI HTTP wrapper (POST /api/chat, GET /health, GET /metrics)"
  - "AIAgent sync-to-async adapter with per-session SQLite locking"
  - "Bearer token auth (HERMES_API_KEY) between Next.js and Hermes"
  - "Next.js chat route rewritten as thin Hermes proxy"
  - "Retry with exponential backoff (5s → 15s → 45s)"
  - "Redis queue fallback with filesystem last-resort"
affects: [15-04-docker-integration]

# Tech tracking
tech-stack:
  added:
    - "FastAPI (Python web framework for Hermes API)"
    - "ioredis (Redis client for Next.js fallback queue)"
  patterns:
    - "Sync-to-async: AIAgent.run_conversation() wrapped in loop.run_in_executor()"
    - "Per-session locking: asyncio.Lock per session_id prevents SQLite 'database is locked'"
    - "Mode injection: Next.js determines PRESALE/ACTIVE/ADMIN from DB, passes via X-Client-Mode header"
    - "Retry + fallback: 3 retries (5s/15s/45s) → Redis queue → filesystem pending_messages.json"
    - "RED metrics: in-memory counters (requests_total, errors_total, latency ring buffer)"

key-files:
  created:
    - AIM/hermes/Dockerfile
    - AIM/hermes/requirements.txt
    - AIM/hermes/app/auth.py
    - AIM/hermes/app/main.py
    - AIM/hermes/app/agent_wrapper.py
  modified:
    - AIM/frontend/app/api/chat/send/route.ts

# Decisions implemented
- D-10: FastAPI wraps Hermes programmatically (not subprocess)
- D-11: Hermes is sole LLM gateway — Next.js proxies all chat here
- D-12: OPERATOR_PROMPT removed from route.ts, moved to SOUL.md
- D-25: Bearer token HERMES_API_KEY for service-to-service auth
- D-26: Next.js determines client mode, passes in X-Client-Mode header
- D-28: ADMIN protection at Next.js layer (NextAuth role=admin)
- D-29: GET /health for Docker healthcheck + Prometheus scraping
- D-30: RED metrics (Rate, Errors, Duration)
- D-33: Redis queue fallback when Hermes unavailable
- D-34: 30s timeout on Hermes calls
- D-35: 3 retries with exponential backoff (5s, 15s, 45s)
- D-36: Filesystem last-resort fallback if Redis also unavailable
