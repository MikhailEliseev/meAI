# Phase 11 Sprint 3: Payment & Onboarding

**Date:** 2026-05-17  
**Status:** Planning  
**Previous Sprint:** Sprint 2 Complete (60h/60h, 192 tests passing)

---

## Sprint Goal

Implement payment processing and automated onboarding workflow with Russian market adaptations.

---

## Sprint Overview

**Duration:** Weeks 5-6 (50 hours)  
**Approach:** Stub Implementation (recommended)  
**Adaptation Time:** +2 hours (5% overhead)

---

## Tasks

### Task 3.1: Payment Integration (14h → 16h with stubs)

**Objective:** Payment processing infrastructure with Russian payment processor stub.

**Implementation Strategy:**

**Option 1: Stub Implementation (Recommended for Sprint 3)**
- Create `HelcimClient` stub with mock interface
- Return success responses for development
- Document TODO for ЮKassa replacement
- Estimated: 2 hours

**Option 2: Full ЮKassa Integration (Phase 12)**
- Real ЮKassa API integration
- Webhook handling
- Payment status tracking
- Estimated: 14 hours (deferred to Phase 12)

**Components:**

1. **Payment Models** (`models/payment.py`):
   - Payment transaction tracking
   - Status: pending, processing, completed, failed, refunded
   - Amount, currency (RUB), payment method
   - Customer info (encrypted)
   - Timestamps and audit trail

2. **Payment Schemas** (`schemas/payment.py`):
   - `PaymentRequest` - Payment initiation
   - `PaymentResponse` - Payment result
   - `PaymentStatus` - Status check
   - `RefundRequest` - Refund processing

3. **Helcim Client Stub** (`services/payment/helcim_client.py`):
   - Mock payment processing
   - Always returns success (for development)
   - Logs all payment attempts
   - TODO comments for ЮKassa replacement

4. **Payment Service** (`services/payment/payment_service.py`):
   - Payment orchestration
   - Transaction logging
   - Status tracking
   - Refund handling

**Test Coverage:**
- 20 tests (stub behavior, transaction logging, status tracking)

**Files to Create:**
- `AIM/src/aim/models/payment.py` (120 lines)
- `AIM/src/aim/schemas/payment.py` (180 lines)
- `AIM/src/aim/services/payment/__init__.py` (30 lines)
- `AIM/src/aim/services/payment/helcim_client.py` (150 lines - STUB)
- `AIM/src/aim/services/payment/payment_service.py` (300 lines)
- `AIM/tests/services/payment/test_helcim_stub.py` (200 lines)
- `AIM/tests/services/payment/test_payment_service.py` (350 lines)

**Adaptation Notes:**
- Currency: USD → RUB
- Payment methods: Russian cards (Visa, Mastercard, Mir)
- Stub returns mock transaction IDs
- Real ЮKassa integration in Phase 12

---

### Task 3.2: Payment UI (8h)

**Objective:** Payment form with Russian payment processor integration.

**Components:**

1. **Payment Form Component** (`components/payment/PaymentForm.tsx`):
   - Card number input (Russian cards)
   - Expiry date and CVV
   - Cardholder name (Cyrillic support)
   - Amount display (RUB)
   - Submit button with loading state

2. **Payment Status Component** (`components/payment/PaymentStatus.tsx`):
   - Success/failure messages
   - Transaction ID display
   - Receipt download link
   - Return to dashboard button

3. **Payment API Integration** (`api/payment.ts`):
   - POST /api/payments/create
   - GET /api/payments/{id}/status
   - POST /api/payments/{id}/refund

**Test Coverage:**
- 15 tests (form validation, submission, status display)

**Files to Create:**
- `AIM/frontend/components/payment/PaymentForm.tsx` (250 lines)
- `AIM/frontend/components/payment/PaymentStatus.tsx` (150 lines)
- `AIM/frontend/api/payment.ts` (120 lines)
- `AIM/frontend/tests/payment/PaymentForm.test.tsx` (200 lines)
- `AIM/frontend/tests/payment/PaymentStatus.test.tsx` (150 lines)

**Adaptation Notes:**
- Russian card validation (Mir support)
- Cyrillic name input
- RUB currency display
- Russian error messages

---

### Task 3.3: AI Document Processing (16h)

**Objective:** Automated document extraction and validation using AI.

**Components:**

1. **Document Processor** (`services/documents/processor.py`):
   - PDF/image upload handling
   - OCR with Tesseract (Russian language)
   - AI extraction with Claude (clinic info, license, contacts)
   - Validation rules (required fields, format checks)
   - Confidence scoring

2. **Document Models** (`models/document.py`):
   - Document metadata (type, status, uploaded_at)
   - Extracted data (JSON field)
   - Validation results
   - Processing status: pending, processing, completed, failed

3. **Document Schemas** (`schemas/document.py`):
   - `DocumentUploadRequest` - Upload parameters
   - `DocumentUploadResponse` - Upload result
   - `ExtractedData` - Parsed document data
   - `ValidationResult` - Validation status

4. **AI Extraction Service** (`services/documents/ai_extractor.py`):
   - Claude API integration
   - Prompt engineering for document types
   - Structured output parsing
   - Confidence scoring

**Test Coverage:**
- 25 tests (OCR, AI extraction, validation, error handling)

**Files to Create:**
- `AIM/src/aim/models/document.py` (150 lines)
- `AIM/src/aim/schemas/document.py` (200 lines)
- `AIM/src/aim/services/documents/__init__.py` (30 lines)
- `AIM/src/aim/services/documents/processor.py` (400 lines)
- `AIM/src/aim/services/documents/ai_extractor.py` (350 lines)
- `AIM/tests/services/documents/test_processor.py` (400 lines)
- `AIM/tests/services/documents/test_ai_extractor.py` (350 lines)

**Dependencies:**
- pytesseract>=0.3.10 (OCR)
- pdf2image>=1.16.0 (PDF to image)
- pillow>=10.0.0 (already installed)

**Adaptation Notes:**
- Russian language OCR (Tesseract rus model)
- Russian document types (медицинская лицензия, ИНН, ОГРН)
- Cyrillic text extraction
- Russian validation rules

---

### Task 3.4: Onboarding Workflow (12h → 14h with stubs)

**Objective:** Automated onboarding with document signing stub.

**Implementation Strategy:**

**Option 1: Stub Implementation (Recommended for Sprint 3)**
- Create `DocuSignClient` stub with mock interface
- Return success responses for development
- Document TODO for Контур.Диадок replacement
- Estimated: 2 hours

**Option 2: Full Контур.Диадок Integration (Phase 12)**
- Real Контур.Диадок API integration
- Electronic signature flow
- Document status tracking
- Estimated: 12 hours (deferred to Phase 12)

**Components:**

1. **Onboarding Models** (`models/onboarding.py`):
   - Onboarding session tracking
   - Steps: payment, documents, signature, completion
   - Status per step
   - Completion timestamp

2. **Onboarding Schemas** (`schemas/onboarding.py`):
   - `OnboardingSession` - Session data
   - `OnboardingStep` - Step status
   - `OnboardingProgress` - Progress tracking

3. **DocuSign Client Stub** (`services/signature/docusign_client.py`):
   - Mock signature request
   - Always returns success (for development)
   - Logs all signature attempts
   - TODO comments for Контур.Диадок replacement

4. **Onboarding Service** (`services/onboarding/onboarding_service.py`):
   - Workflow orchestration
   - Step validation
   - Progress tracking
   - Completion notification

**Test Coverage:**
- 20 tests (workflow steps, validation, completion)

**Files to Create:**
- `AIM/src/aim/models/onboarding.py` (150 lines)
- `AIM/src/aim/schemas/onboarding.py` (180 lines)
- `AIM/src/aim/services/signature/__init__.py` (30 lines)
- `AIM/src/aim/services/signature/docusign_client.py` (150 lines - STUB)
- `AIM/src/aim/services/onboarding/__init__.py` (30 lines)
- `AIM/src/aim/services/onboarding/onboarding_service.py` (400 lines)
- `AIM/tests/services/signature/test_docusign_stub.py` (200 lines)
- `AIM/tests/services/onboarding/test_onboarding_service.py` (400 lines)

**Adaptation Notes:**
- DocuSign → Контур.Диадок (stub for now)
- Russian contract templates
- ФЗ-152 consent in onboarding flow
- Russian notification messages

---

## Total Estimates

**Development Time:**
- Task 3.1: Payment Integration (stub) - 16h
- Task 3.2: Payment UI - 8h
- Task 3.3: AI Document Processing - 16h
- Task 3.4: Onboarding Workflow (stub) - 14h
- **Total:** 54 hours (50h base + 4h stubs)

**Test Coverage:**
- Task 3.1: 20 tests
- Task 3.2: 15 tests
- Task 3.3: 25 tests
- Task 3.4: 20 tests
- **Total:** 80 tests

**Files to Create:**
- 30 files
- ~5,500 lines of code

---

## Dependencies

**Required:**
- ✅ Phase 11 Sprint 2 Complete (Lead Capture, Scoring, Linear, Email, Analytics)
- ✅ LLM Orchestrator (Phase 10 Task 1.1)
- ✅ SendGrid Email (Phase 9)

**New Dependencies:**
- pytesseract>=0.3.10 (OCR)
- pdf2image>=1.16.0 (PDF processing)
- tesseract-ocr (system package, Russian language model)

---

## Russian Market Adaptations

**Payment:**
- ✅ Helcim stub → Replace with ЮKassa in Phase 12
- ✅ Currency: RUB
- ✅ Russian card support (Visa, Mastercard, Mir)

**Document Processing:**
- ✅ Russian OCR (Tesseract rus model)
- ✅ Russian document types (лицензия, ИНН, ОГРН)
- ✅ Cyrillic text extraction

**Onboarding:**
- ✅ DocuSign stub → Replace with Контур.Диадок in Phase 12
- ✅ Russian contract templates
- ✅ ФЗ-152 consent flow

---

## Success Metrics

**Payment:**
- Stub success rate: 100% (mock)
- Transaction logging: 100%
- Error handling: comprehensive

**Document Processing:**
- OCR accuracy: >90% (Russian text)
- AI extraction accuracy: >85%
- Processing time: <60s per document

**Onboarding:**
- Workflow completion rate: >80%
- Step validation: 100%
- Stub success rate: 100% (mock)

---

## Risk Mitigation

**Risk 1: OCR Accuracy for Russian Documents**
- Mitigation: Use Tesseract rus model, manual review for low confidence

**Risk 2: AI Extraction Errors**
- Mitigation: Confidence scoring, human review for <80% confidence

**Risk 3: Stub Limitations**
- Mitigation: Clear documentation, Phase 12 replacement plan

---

## Next Steps

1. ✅ Review Sprint 3 plan
2. ⏳ Install dependencies (pytesseract, pdf2image, tesseract-ocr)
3. ⏳ Start Task 3.1: Payment Integration (stub)
4. ⏳ Create Linear tasks for Sprint 3

---

## Phase 12 Replacement Plan

**Payment Integration:**
- Replace Helcim stub with ЮKassa
- Implement webhook handling
- Test payment flow end-to-end
- Estimated: 14 hours

**Signature Integration:**
- Replace DocuSign stub with Контур.Диадок
- Implement signature flow
- Test onboarding end-to-end
- Estimated: 12 hours

**Total Phase 12:** 26 hours (payment + signature)

