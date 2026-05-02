# meAI Documentation

> Complete documentation for meAI - AI Agency Architect

## 📚 Getting Started

- [README](../README.md) — Project overview and quick start
- [Installation Guide](installation.md) — Detailed setup instructions
- [Architecture Overview](architecture/overview.md) — System design

---

## 📖 Tutorials

Step-by-step guides for common tasks:

1. [Creating Your First Agent](tutorials/01-first-agent.md) — Build an SEO agent from scratch
2. [Memory System](tutorials/02-memory-system.md) — Working with Obsidian vaults
3. [Event Sourcing](tutorials/03-event-sourcing.md) — Logging and replaying events
4. [Rollback & Recovery](tutorials/04-rollback.md) — Using checkpoints

---

## 🔧 API Reference

Complete API documentation for all components:

### Core Components

- [Architect](api/architect.md) — Autonomous decision making
- [Decision Maker](api/decision-maker.md) — Strategy selection with learning
- [Orchestrator](api/orchestrator.md) — Async coordination and workflows
- [Rollback Manager](api/rollback.md) — Snapshot + event replay recovery

### Storage Layer

- [Database](api/database.md) — SQLite async operations
- [Event Store](api/event-store.md) — Event sourcing and replay
- [Event Bus](api/event-bus.md) — Async message queue
- [Obsidian Vault](api/obsidian.md) — Memory management

### Agent System

- [Agent Factory](api/agent-factory.md) — Creating and managing agents
- [Prompt Generator](api/prompt-generator.md) — Generating agent prompts
- [System Registry](api/system-registry.md) — SYSTEM.md management

### Safety & Monitoring

- [Loop Detector](api/loop-detector.md) — Preventing infinite delegation
- [Timeout Manager](api/timeout-manager.md) — Operation timeouts
- [Context Monitor](api/context-monitor.md) — 40% rule enforcement
- [Health Checker](api/health.md) — Component health monitoring
- [Metrics Collector](api/metrics.md) — Performance metrics

---

## 🏗️ Architecture

System design and patterns:

- [Overview](architecture/overview.md) — High-level architecture
- [Storage Layer](architecture/storage.md) — Dual storage (SQLite + Obsidian)
- [Event Sourcing](architecture/event-sourcing.md) — Immutable audit log
- [Agent System](architecture/agents.md) — Agent hierarchy and communication
- [Safety Mechanisms](architecture/safety.md) — Loop detection, timeouts, context

---

## 📋 Architecture Decision Records (ADR)

Why we made certain design choices:

- [ADR-001: Dual Storage](adr/001-dual-storage.md) — SQLite + Obsidian
- [ADR-002: Event Sourcing](adr/002-event-sourcing.md) — Immutable log
- [ADR-003: Async First](adr/003-async-first.md) — Full asyncio
- [ADR-004: TDD Approach](adr/004-tdd-approach.md) — Test-driven development
- [ADR-005: Obsidian for Memory](adr/005-obsidian-memory.md) — Why Obsidian

---

## 🧪 Testing

- [Testing Guide](testing/guide.md) — How to write tests
- [Test Coverage](testing/coverage.md) — Current coverage report
- [Integration Tests](testing/integration.md) — End-to-end testing

---

## 🚀 Deployment

- [Docker Setup](deployment/docker.md) — Containerization
- [Production Guide](deployment/production.md) — Production deployment
- [Monitoring](deployment/monitoring.md) — Health checks and metrics

---

## 🔍 How-To Guides

Practical guides for specific tasks:

- [How to Create an Agent](how-to/create-agent.md)
- [How to Use Decision Maker](how-to/use-decision-maker.md)
- [How to Handle Errors](how-to/error-handling.md)
- [How to Optimize Performance](how-to/performance.md)
- [How to Debug Issues](how-to/debugging.md)

---

## 📊 Examples

Complete working examples:

- [Simple Agent](examples/simple-agent.py) — Basic agent creation
- [Decision Making](examples/decision-making.py) — Using Architect
- [Event Sourcing](examples/event-sourcing.py) — Logging events
- [Rollback Demo](examples/rollback-demo.py) — Checkpoint and recovery
- [Full Workflow](examples/full-workflow.py) — Complete example

---

## 🤝 Contributing

- [Contributing Guide](contributing.md) — How to contribute
- [Code Style](code-style.md) — Coding conventions
- [Development Setup](development.md) — Dev environment

---

## 📝 Reference

- [Glossary](reference/glossary.md) — Terms and definitions
- [FAQ](reference/faq.md) — Frequently asked questions
- [Troubleshooting](reference/troubleshooting.md) — Common issues
- [Changelog](../CHANGELOG.md) — Version history

---

## 📈 Status

**Current Version:** 0.1.0  
**Status:** ✅ Production Ready  
**Tests:** 133/133 passing  
**Coverage:** ~80%+  
**Last Updated:** 2026-05-02

---

## 🔗 Quick Links

- [GitHub Repository](https://github.com/mikhaileliseev/meai)
- [Issue Tracker](https://github.com/mikhaileliseev/meai/issues)
- [Discussions](https://github.com/mikhaileliseev/meai/discussions)
- [Releases](https://github.com/mikhaileliseev/meai/releases)

---

## 📧 Support

- **Email:** me@mikhaileliseev.com
- **Project:** meAI - AI Agency Architect
- **Domain:** iamaim.ru

---

**Built with ❤️ by Mikhail Eliseev**
