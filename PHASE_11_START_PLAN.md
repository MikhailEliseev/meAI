# Phase 11: Client Acquisition - Start Plan

**Date:** 2026-05-16  
**Status:** Ready to Start  
**Previous Phase:** Phase 10 (57% complete, 4/7 tasks)

---

## Executive Summary

Phase 11 фокусируется на client acquisition infrastructure для медицинского маркетингового агентства. План включает 8 недель работы (200 часов), разделённых на 4 фазы.

**Критическая адаптация:** План создан для западного рынка, требует адаптации под российскую юрисдикцию.

---

## Russian Market Adaptation

### Что НЕ применяется в России:

**Payment Processors:**
- ❌ Helcim - не работает в РФ
- ⚠️ Замена: ЮKassa (Яндекс), CloudPayments, Тинькoff Acquiring, Сбербанк Acquiring

**Document Signing:**
- ❌ DocuSign - работает, но дорого и не популярно в РФ
- ⚠️ Замена: Контур.Диадок, СБИС, Такском (российские ЭЦП)

**Compliance:**
- ❌ HIPAA (США) - не применяется в РФ
- ⚠️ Замена: ФЗ-152 "О персональных данных", ФЗ-323 "Об охране здоровья"

### Что применяется (технические решения):

**Архитектурные паттерны (берём с Запада):**
- ✅ AI Lead Scoring (30+ факторов)
- ✅ Automated Onboarding (AI document processing)
- ✅ Conversion-optimized Landing Pages
- ✅ Real-time Analytics
- ✅ Email automation workflows

**Технологии (берём с Запада):**
- ✅ Next.js 14, React, TypeScript
- ✅ FastAPI, Python, PostgreSQL
- ✅ Redis, Docker
- ✅ OpenAI, Claude (LLM)
- ✅ SendGrid (работает в РФ, уже используем в Phase 9)

---

## Adapted Plan for Russian Market

### Phase 1: Landing Page (Weeks 1-2, 40 hours) ✅ NO CHANGES

**Tasks:**
- Task 1.1: Hero Section (6h) - ✅ Применяется как есть
- Task 1.2: Social Proof (8h) - ✅ Применяется как есть
- Task 1.3: Process Visualization (6h) - ✅ Применяется как есть
- Task 1.4: FAQ Section (6h) - ⚠️ Адаптировать вопросы под ФЗ-152 вместо HIPAA
- Task 1.5: Contact Form (10h) - ⚠️ Адаптировать consent под ФЗ-152
- Task 1.6: Integration (4h) - ✅ Применяется как есть

**Adaptation Notes:**
- FAQ: Заменить HIPAA вопросы на ФЗ-152 вопросы
- Contact Form: HIPAA consent → ФЗ-152 consent (согласие на обработку персональных данных)
- Trust badges: HIPAA badges → ФЗ-152 compliance badges

**Estimated Adaptation Time:** +2 hours (FAQ + Form consent)

---

### Phase 2: Lead Generation (Weeks 3-4, 60 hours) ✅ MOSTLY NO CHANGES

**Tasks:**
- Task 2.1: Lead Capture Service (12h) - ⚠️ ФЗ-152 consent вместо HIPAA
- Task 2.2: AI Lead Scoring (16h) - ✅ Применяется как есть
- Task 2.3: Linear Integration (12h) - ✅ Применяется как есть (Phase 7.5 уже работает)
- Task 2.4: Email Automation (10h) - ✅ Применяется как есть (SendGrid работает в РФ)
- Task 2.5: Analytics Dashboard (10h) - ✅ Применяется как есть

**Adaptation Notes:**
- Lead Capture: HIPAA consent validation → ФЗ-152 consent validation
- Encryption: AES-256 (применяется как есть)
- Audit logging: Адаптировать под требования ФЗ-152

**Estimated Adaptation Time:** +3 hours (consent validation + audit logging)

---

### Phase 3: Payment & Onboarding (Weeks 5-6, 50 hours) ⚠️ MAJOR CHANGES

**Tasks:**
- Task 3.1: Payment Integration (14h) - 🔴 CRITICAL: Helcim → ЮKassa/CloudPayments
- Task 3.2: Payment UI (8h) - ⚠️ Адаптировать под российский процессор
- Task 3.3: AI Document Processing (16h) - ✅ Применяется как есть
- Task 3.4: Onboarding Workflow (12h) - ⚠️ DocuSign → Контур.Диадок (или заглушка)

**Adaptation Strategy:**

#### Option 1: Full Implementation (Recommended)
- Replace Helcim with ЮKassa (Яндекс)
- Replace DocuSign with Контур.Диадок
- Estimated time: +10 hours (API integration + testing)

#### Option 2: Stub Implementation (Faster)
- Create payment stub (mock Helcim interface)
- Create signature stub (mock DocuSign interface)
- Implement real integrations later (Phase 12)
- Estimated time: +2 hours (stubs only)

**Recommendation:** Option 2 (Stub) для первого запуска, Option 1 для production.

**Estimated Adaptation Time:** +2 hours (stubs) or +10 hours (full)

---

### Phase 4: Testing & Launch (Weeks 7-8, 50 hours) ⚠️ MINOR CHANGES

**Tasks:**
- Task 4.1: E2E Testing (16h) - ✅ Применяется как есть
- Task 4.2: Security Audit (12h) - ⚠️ HIPAA → ФЗ-152 compliance audit
- Task 4.3: Performance Optimization (10h) - ✅ Применяется как есть
- Task 4.4: Monitoring & Alerting (8h) - ✅ Применяется как есть
- Task 4.5: Documentation (4h) - ⚠️ Адаптировать под российские требования

**Adaptation Notes:**
- Security Audit: Проверка соответствия ФЗ-152 вместо HIPAA
- Documentation: Российские законы и практики

**Estimated Adaptation Time:** +3 hours (audit + docs)

---

## Total Adaptation Time

**Option 1 (Full Implementation):**
- Phase 1: +2 hours
- Phase 2: +3 hours
- Phase 3: +10 hours (full payment + signature)
- Phase 4: +3 hours
- **Total:** +18 hours (9% overhead)

**Option 2 (Stub Implementation - Recommended):**
- Phase 1: +2 hours
- Phase 2: +3 hours
- Phase 3: +2 hours (stubs only)
- Phase 4: +3 hours
- **Total:** +10 hours (5% overhead)

---

## Recommended Approach

### Step 1: Start with Stub Implementation
**Duration:** 8 weeks + 10 hours = 210 hours total

**Rationale:**
- Быстрый запуск (5% overhead вместо 9%)
- Технические паттерны работают сразу
- Payment и signature можно заменить позже
- Фокус на core functionality (landing page, lead scoring, automation)

**Stubs to Create:**
- `AIM/src/aim/services/payment/helcim_client.py` (STUB)
- `AIM/src/aim/services/signature/docusign_client.py` (STUB)

**Documentation:**
- Пометить stubs как "TODO: Replace with ЮKassa/Контур.Диадок"
- Создать задачи в backlog для замены

### Step 2: Replace Stubs in Phase 12
**Duration:** 2-3 weeks

**Tasks:**
- Replace Helcim stub with ЮKassa integration
- Replace DocuSign stub with Контур.Диадок integration
- Test payment flow end-to-end
- Test signature flow end-to-end

---

## Dependencies Check

### Phase 8: Multi-tenant Frontend ✅ COMPLETED
- Next.js 14 infrastructure ready
- Dashboard components available
- Authentication working

### Phase 7.5: Linear Integration ✅ COMPLETED
- Linear API client ready
- Task creation working
- Custom fields supported

### Phase 9: SendGrid Email ✅ COMPLETED
- Email sending working
- Templates supported
- Webhooks configured

### Phase 10: AI Enhancement ✅ PARTIALLY COMPLETED (57%)
- LLM Orchestrator ready (Task 1.1)
- Ad Copy Generator ready (Task 2.1)
- Predictive Analytics ready (Task 2.2)
- Magisters Integration ready (Task 2.3)

**All dependencies satisfied for Phase 11 start.**

---

## First Sprint Plan (Week 1-2)

### Sprint Goal: Launch Landing Page

**Tasks:**
1. Task 1.1: Hero Section (6h)
2. Task 1.2: Social Proof (8h)
3. Task 1.3: Process Visualization (6h)
4. Task 1.4: FAQ Section (6h + 1h adaptation)
5. Task 1.5: Contact Form (10h + 1h adaptation)
6. Task 1.6: Integration (4h)

**Total:** 42 hours (40h base + 2h adaptation)

**Deliverable:** Conversion-optimized landing page with ФЗ-152 compliance

---

## Risk Mitigation

### Risk 1: Payment Integration Complexity
**Mitigation:** Use stub implementation first, replace later

### Risk 2: ФЗ-152 Compliance Uncertainty
**Mitigation:** Consult with legal expert (budget $2-5K)

### Risk 3: AI Lead Scoring Inaccuracy
**Mitigation:** Validate against historical data, human review for first 100 leads

### Risk 4: Integration Failures (Linear, SendGrid)
**Mitigation:** Comprehensive tests, retry logic, fallback to manual

---

## Success Metrics

**Landing Page:**
- Lighthouse score ≥90 (all categories)
- Conversion rate ≥3% (industry average: 2-5%)
- Page load time <2s (3G)

**Lead Generation:**
- Lead capture success rate >95%
- AI scoring accuracy >75%
- Email delivery rate >98%

**Payment & Onboarding:**
- Payment success rate >99% (when implemented)
- Onboarding completion rate >80%
- Document processing time <60s

---

## Next Steps

1. ✅ Review this adaptation plan
2. ✅ Confirm stub implementation approach
3. ✅ Start Sprint 1 (Landing Page)
4. ⏳ Create tasks in Linear for Sprint 1
5. ⏳ Begin Task 1.1 (Hero Section)

---

## Questions for User

1. **Payment Integration:** Согласен с stub implementation для первого запуска?
2. **Legal Consultation:** Нужна ли консультация юриста по ФЗ-152? (бюджет $2-5K)
3. **Priority:** Начинаем Phase 11 сейчас или доделываем Phase 10 (Tasks 3.1-3.3)?

---

## Recommendation

**✅ START PHASE 11 NOW**

**Rationale:**
- Phase 10 базовая инфраструктура готова (57%)
- Phase 11 критичнее для бизнеса (client acquisition)
- Stub implementation позволяет быстрый старт
- Phase 10 Tasks 3.1-3.3 можно доделать позже

**First Action:** Create Sprint 1 tasks in Linear and start Task 1.1 (Hero Section).
