---
task: 2.4
phase: 11
sprint: 2
name: Email Automation Workflows
status: planning
created: 2026-05-16T19:56:54Z
estimated_hours: 10
---

# Task 2.4: Email Automation Workflows

## Goal

Implement automated email campaigns for leads based on their tier (Hot/Warm/Cold) with personalized content, multi-step sequences, and tracking.

## Context

**Current State:**
- ✅ Lead Capture Service (Task 2.1) - capturing leads with ФЗ-152 compliance
- ✅ AI Lead Scoring (Task 2.2) - scoring leads into Hot/Warm/Cold tiers
- ✅ Linear Integration (Task 2.3) - creating tasks for Hot/Warm leads
- ✅ SendGrid integration exists (from Phase 9)
- ⏳ Email automation workflows - NOT IMPLEMENTED

**What We're Building:**
Automated email workflows that:
- Trigger based on lead tier (Hot/Warm/Cold)
- Send personalized multi-step sequences
- Track opens, clicks, conversions
- Handle unsubscribes and bounces
- Integrate with AI for content generation

## Requirements

### Functional Requirements

**FR-1: Email Workflow Engine**
- Trigger workflows based on lead tier
- Support multi-step sequences (Day 0, 3, 7, etc.)
- Schedule emails with APScheduler or BullMQ
- Retry failed sends with exponential backoff
- Track workflow state (pending, sent, opened, clicked, converted)

**FR-2: Email Templates**
- Hot lead: Instant personalized email (within 5 min)
  - Subject: "Ваш запрос на [услуга] получен"
  - Content: Персонализированное предложение, контакты менеджера
  - CTA: "Записаться на консультацию"
- Warm nurture: 3-email sequence
  - Day 0: Welcome + value proposition
  - Day 3: Case study + social proof
  - Day 7: Special offer + urgency
- Cold nurture: Weekly digest
  - Educational content
  - Industry news
  - Soft CTA
- HTML + plain text versions
- Responsive design (mobile-first)

**FR-3: Personalization**
- AI-generated content based on:
  - Lead specialty (стоматология, пластическая хирургия, etc.)
  - Lead source (landing page, referral, etc.)
  - Lead behavior (pages visited, time on site)
- Dynamic fields: {name}, {specialty}, {service}, {manager_name}
- A/B testing support (2 variants per email)

**FR-4: Tracking & Analytics**
- Email events: sent, delivered, opened, clicked, bounced, complained, unsubscribed
- Conversion tracking (lead → client)
- Campaign performance metrics (open rate, click rate, conversion rate)
- Integration with Analytics Dashboard (Task 2.5)

**FR-5: Compliance**
- ФЗ-152 compliance (consent tracking)
- Unsubscribe link in every email
- Bounce handling (hard bounce → remove, soft bounce → retry)
- Complaint handling (spam report → immediate unsubscribe)

### Non-Functional Requirements

**NFR-1: Performance**
- Send hot lead email within 5 minutes of capture
- Process 1000+ emails per hour
- Email delivery rate > 95%
- Open rate target: 25-35% (medical industry average)

**NFR-2: Reliability**
- Retry failed sends (3 attempts with exponential backoff)
- Dead letter queue for permanently failed emails
- Idempotency (don't send duplicate emails)
- Graceful degradation (if SendGrid down, queue emails)

**NFR-3: Scalability**
- Support 10,000+ leads in database
- Handle 100+ concurrent workflows
- Horizontal scaling with Redis-backed queue

## Architecture

### Components

```
LeadEmailAutomationService
├── WorkflowEngine
│   ├── trigger_workflow(lead_id, tier)
│   ├── schedule_email(workflow_id, email_id, send_at)
│   └── process_scheduled_emails()
├── EmailTemplateRenderer
│   ├── render_template(template_id, context)
│   ├── personalize_content(lead, template)
│   └── generate_ai_content(lead, prompt)
├── EmailSender
│   ├── send_email(to, subject, html, text)
│   ├── track_event(email_id, event_type)
│   └── handle_webhook(event)
└── WorkflowStateManager
    ├── get_workflow_state(workflow_id)
    ├── update_workflow_state(workflow_id, state)
    └── get_next_email(workflow_id)
```

### Database Schema

```sql
-- Email workflows
CREATE TABLE email_workflows (
    id UUID PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    tier VARCHAR(10) NOT NULL,  -- hot, warm, cold
    status VARCHAR(20) NOT NULL,  -- active, paused, completed, cancelled
    current_step INT DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scheduled emails
CREATE TABLE scheduled_emails (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES email_workflows(id),
    template_id VARCHAR(50) NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- pending, sent, failed, cancelled
    retry_count INT DEFAULT 0,
    sendgrid_message_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Email events (tracking)
CREATE TABLE email_events (
    id UUID PRIMARY KEY,
    email_id UUID REFERENCES scheduled_emails(id),
    event_type VARCHAR(20) NOT NULL,  -- sent, delivered, opened, clicked, bounced, complained, unsubscribed
    event_data JSONB,
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Email templates
CREATE TABLE email_templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    tier VARCHAR(10) NOT NULL,
    step INT NOT NULL,
    subject_template TEXT NOT NULL,
    html_template TEXT NOT NULL,
    text_template TEXT NOT NULL,
    ai_prompt TEXT,  -- for AI content generation
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Workflow State Machine

```
Hot Lead Workflow:
  pending → email_0_sent → email_0_opened → email_0_clicked → converted
                        → email_0_bounced → failed

Warm Lead Workflow:
  pending → email_0_sent → email_1_scheduled → email_1_sent → email_2_scheduled → email_2_sent → completed
                        → unsubscribed → cancelled

Cold Lead Workflow:
  pending → email_0_sent → email_1_scheduled (7 days) → email_1_sent → ... → completed
                        → unsubscribed → cancelled
```

## Implementation Plan

### Step 1: Database Models (1h)

**Files to create:**
- `AIM/src/aim/models/email_workflow.py` - EmailWorkflow model
- `AIM/src/aim/models/scheduled_email.py` - ScheduledEmail model
- `AIM/src/aim/models/email_event.py` - EmailEvent model
- `AIM/src/aim/models/email_template.py` - EmailTemplate model

**Tasks:**
1. Create SQLAlchemy models with relationships
2. Add to `models/__init__.py` exports
3. Create Alembic migration
4. Run migration to create tables

### Step 2: Email Templates (2h)

**Files to create:**
- `AIM/src/aim/services/email/templates/hot_instant.html`
- `AIM/src/aim/services/email/templates/warm_day0.html`
- `AIM/src/aim/services/email/templates/warm_day3.html`
- `AIM/src/aim/services/email/templates/warm_day7.html`
- `AIM/src/aim/services/email/templates/cold_weekly.html`
- `AIM/src/aim/services/email/template_renderer.py`

**Tasks:**
1. Design HTML templates (responsive, mobile-first)
2. Create plain text versions
3. Add dynamic fields ({name}, {specialty}, etc.)
4. Implement TemplateRenderer with Jinja2
5. Add AI content generation (optional personalization)

### Step 3: Workflow Engine (3h)

**Files to create:**
- `AIM/src/aim/services/email/workflow_engine.py`
- `AIM/src/aim/services/email/workflow_state_manager.py`
- `AIM/src/aim/services/email/scheduler.py`

**Tasks:**
1. Implement WorkflowEngine:
   - `trigger_workflow(lead_id, tier)` - start workflow for lead
   - `schedule_email(workflow_id, email_id, send_at)` - schedule email
   - `process_scheduled_emails()` - send due emails (cron job)
2. Implement WorkflowStateManager:
   - Track workflow state (current step, status)
   - Get next email in sequence
   - Handle state transitions
3. Implement Scheduler:
   - APScheduler or BullMQ integration
   - Cron job to process scheduled emails every 5 minutes
   - Retry logic with exponential backoff

### Step 4: Email Sender & Tracking (2h)

**Files to create:**
- `AIM/src/aim/services/email/email_sender.py`
- `AIM/src/aim/services/email/webhook_handler.py`

**Tasks:**
1. Implement EmailSender:
   - Send email via SendGrid API
   - Track sent emails in database
   - Handle SendGrid errors (rate limit, invalid email, etc.)
2. Implement WebhookHandler:
   - Receive SendGrid webhooks (delivered, opened, clicked, bounced, etc.)
   - Store events in email_events table
   - Update workflow state based on events
   - Handle unsubscribes and complaints

### Step 5: Integration & Testing (2h)

**Files to create:**
- `AIM/tests/services/email/test_workflow_engine.py`
- `AIM/tests/services/email/test_email_sender.py`
- `AIM/tests/services/email/test_template_renderer.py`
- `AIM/tests/services/email/test_webhook_handler.py`

**Tasks:**
1. Unit tests for WorkflowEngine (15 tests)
2. Unit tests for EmailSender (10 tests)
3. Unit tests for TemplateRenderer (8 tests)
4. Integration test: full workflow (hot lead → email sent → opened → clicked)
5. Mock SendGrid API for tests

## Success Criteria

**Functionality:**
- [ ] Hot lead receives email within 5 minutes
- [ ] Warm lead receives 3-email sequence (Day 0, 3, 7)
- [ ] Cold lead receives weekly digest
- [ ] All emails are personalized with AI content
- [ ] Unsubscribe link works
- [ ] Bounces and complaints are handled

**Performance:**
- [ ] Email delivery rate > 95%
- [ ] Hot lead email sent within 5 minutes
- [ ] Process 1000+ emails per hour

**Quality:**
- [ ] 40+ tests passing
- [ ] All email templates render correctly (HTML + text)
- [ ] Workflow state machine works correctly
- [ ] SendGrid webhooks processed correctly

## Dependencies

**External:**
- SendGrid API (already integrated in Phase 9)
- APScheduler or BullMQ (for scheduling)
- Jinja2 (for template rendering)
- Redis (for queue, optional)

**Internal:**
- Lead model (Task 2.1)
- LeadScoringService (Task 2.2)
- Database (SQLAlchemy async)

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SendGrid rate limits | High | Implement queue with rate limiting |
| Email deliverability (spam) | High | Warm up domain, use SPF/DKIM/DMARC |
| Template rendering errors | Medium | Extensive testing, fallback to plain text |
| Workflow state bugs | Medium | State machine tests, idempotency |
| AI content generation cost | Low | Cache generated content, use cheaper model |

## Russian Market Adaptation

**Применяется:**
- ✅ SendGrid (работает в РФ, уже используем)
- ✅ Email templates на русском языке
- ✅ ФЗ-152 compliance (consent tracking, unsubscribe)

**Адаптируется:**
- ⚠️ Email content: медицинские услуги (не HIPAA, а ФЗ-323)
- ⚠️ Timing: учитывать московское время (GMT+3)

**Откладывается:**
- ⏸️ SMS integration (Phase 12, российские провайдеры)

## Next Steps

1. **Immediate:**
   - Create database models and migration
   - Design email templates (HTML + text)
   - Implement WorkflowEngine core logic

2. **After Task 2.4:**
   - Task 2.5: Analytics Dashboard (visualize email metrics)
   - Phase 11 Sprint 3: Payment Integration

3. **Future Improvements:**
   - A/B testing for email variants
   - Advanced personalization (ML-based)
   - SMS integration for hot leads
   - WhatsApp integration (if available in Russia)

## Estimated Time Breakdown

| Step | Description | Time |
|------|-------------|------|
| 1 | Database models & migration | 1h |
| 2 | Email templates (HTML + text) | 2h |
| 3 | Workflow engine & scheduler | 3h |
| 4 | Email sender & webhook handler | 2h |
| 5 | Testing & integration | 2h |
| **Total** | | **10h** |

## Files to Create (15 files)

**Models (4 files):**
- `models/email_workflow.py`
- `models/scheduled_email.py`
- `models/email_event.py`
- `models/email_template.py`

**Templates (5 files):**
- `services/email/templates/hot_instant.html`
- `services/email/templates/warm_day0.html`
- `services/email/templates/warm_day3.html`
- `services/email/templates/warm_day7.html`
- `services/email/templates/cold_weekly.html`

**Services (4 files):**
- `services/email/workflow_engine.py`
- `services/email/email_sender.py`
- `services/email/template_renderer.py`
- `services/email/webhook_handler.py`

**Tests (4 files):**
- `tests/services/email/test_workflow_engine.py`
- `tests/services/email/test_email_sender.py`
- `tests/services/email/test_template_renderer.py`
- `tests/services/email/test_webhook_handler.py`

**Migration (1 file):**
- `alembic/versions/xxx_add_email_automation_tables.py`

---

## Ready to Start?

План готов! Начинаем с Step 1: Database Models?

Или хочешь:
- Уточнить детали плана?
- Изменить приоритеты?
- Добавить что-то ещё?

Жду команды "поехали" для старта Task 2.4! 🚀
