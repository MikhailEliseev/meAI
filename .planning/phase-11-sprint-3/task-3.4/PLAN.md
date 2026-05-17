# Task 3.4: Onboarding Workflow

**Estimated Time:** 14 hours  
**Status:** Planning  
**Date:** 2026-05-17

## Overview

Orchestrate complete clinic onboarding workflow integrating lead capture, document processing, and payment.

## Architecture

```
Onboarding Workflow
├── Step 1: Lead Capture (existing)
│   └── Lead created with contact info
├── Step 2: Document Upload (Task 3.3)
│   ├── Upload license
│   ├── Upload INN
│   ├── Upload OGRN
│   └── Upload contract
├── Step 3: Document Validation
│   ├── Check all required documents uploaded
│   ├── Check all documents processed successfully
│   └── Check all documents valid
├── Step 4: Payment Processing (Task 3.1)
│   ├── Calculate onboarding fee
│   ├── Process payment
│   └── Confirm payment
└── Step 5: Onboarding Complete
    ├── Update lead status
    ├── Send confirmation email
    └── Create clinic account
```

## Components

### 1. Onboarding State Machine

**File:** `AIM/src/aim/services/onboarding/state_machine.py` (300 lines)

**States:**
- `LEAD_CREATED` - Initial state after lead capture
- `DOCUMENTS_PENDING` - Waiting for document uploads
- `DOCUMENTS_UPLOADED` - All documents uploaded, processing
- `DOCUMENTS_VALIDATED` - All documents processed and valid
- `PAYMENT_PENDING` - Waiting for payment
- `PAYMENT_PROCESSING` - Payment in progress
- `PAYMENT_COMPLETED` - Payment successful
- `ONBOARDING_COMPLETE` - All steps complete
- `ONBOARDING_FAILED` - Onboarding failed (validation/payment)

**Transitions:**
- `upload_document()` - Upload document
- `validate_documents()` - Check all documents valid
- `process_payment()` - Process payment
- `complete_onboarding()` - Finalize onboarding
- `fail_onboarding()` - Mark as failed

**Methods:**
- `get_current_state()` - Get current state
- `can_transition()` - Check if transition allowed
- `transition()` - Execute state transition
- `get_next_steps()` - Get required next steps
- `get_progress()` - Get completion percentage

### 2. Onboarding Service

**File:** `AIM/src/aim/services/onboarding/onboarding_service.py` (400 lines)

**Methods:**
- `start_onboarding(lead_id)` - Initialize onboarding for lead
- `upload_document(lead_id, document_type, file)` - Upload and process document
- `check_documents_complete(lead_id)` - Check all required documents uploaded
- `validate_documents(lead_id)` - Validate all documents
- `calculate_onboarding_fee(lead_id)` - Calculate fee based on documents
- `process_payment(lead_id, payment_data)` - Process onboarding payment
- `complete_onboarding(lead_id)` - Finalize onboarding
- `get_onboarding_status(lead_id)` - Get current status and progress
- `retry_failed_step(lead_id, step)` - Retry failed step

**Business Logic:**
- Required documents: license, inn, ogrn, contract
- Onboarding fee: 50,000 RUB (configurable)
- Document validation: all must be valid
- Payment validation: must be completed
- Email notifications: document uploaded, validation complete, payment received, onboarding complete

### 3. Onboarding Model

**File:** `AIM/src/aim/models/onboarding.py` (120 lines)

**Fields:**
- `id` - Onboarding ID (onb_YYYYMMDDHHMMSS_random)
- `lead_id` - Lead ID (FK)
- `state` - Current state
- `progress` - Completion percentage (0-100)
- `documents_uploaded` - JSON list of uploaded document IDs
- `documents_validated` - Boolean
- `payment_id` - Payment ID (FK, nullable)
- `onboarding_fee` - Fee amount in RUB
- `started_at` - Start timestamp
- `completed_at` - Completion timestamp (nullable)
- `failed_at` - Failure timestamp (nullable)
- `failure_reason` - Failure reason (nullable)
- `metadata` - JSON metadata

**Indexes:**
- lead_id
- state
- started_at

### 4. Onboarding Schemas

**File:** `AIM/src/aim/schemas/onboarding.py` (200 lines)

**Schemas:**
- `OnboardingStartRequest` - Start onboarding request
- `OnboardingStartResponse` - Start response with onboarding_id
- `OnboardingStatusResponse` - Status with state, progress, next_steps
- `OnboardingDocumentUploadRequest` - Document upload request
- `OnboardingDocumentUploadResponse` - Upload response
- `OnboardingPaymentRequest` - Payment request
- `OnboardingPaymentResponse` - Payment response
- `OnboardingCompleteResponse` - Completion response

### 5. Onboarding API Endpoints

**File:** `AIM/src/aim/api/onboarding.py` (350 lines)

**Endpoints:**
- `POST /api/onboarding/start` - Start onboarding for lead
- `GET /api/onboarding/{onboarding_id}/status` - Get status
- `POST /api/onboarding/{onboarding_id}/documents` - Upload document
- `POST /api/onboarding/{onboarding_id}/payment` - Process payment
- `POST /api/onboarding/{onboarding_id}/complete` - Complete onboarding
- `POST /api/onboarding/{onboarding_id}/retry` - Retry failed step
- `GET /api/onboarding/lead/{lead_id}` - Get onboarding for lead

### 6. Database Migration

**File:** `AIM/alembic/versions/004_onboarding_table.py` (60 lines)

**Table:** `onboardings`
- All fields from Onboarding model
- Indexes: lead_id, state, started_at

### 7. Tests

**File:** `AIM/tests/services/test_onboarding.py` (500 lines)

**Test Coverage:**
- State machine: 10 tests (transitions, validation, progress)
- Onboarding service: 15 tests (start, upload, validate, payment, complete, retry)
- API endpoints: 10 tests (all endpoints)
- **Total: 35 tests**

## Implementation Steps

### Step 1: Onboarding Model (1.5h)
- Create Onboarding model with state tracking
- Add indexes
- Generate ID method

### Step 2: Onboarding Schemas (2h)
- Create Pydantic schemas for all requests/responses
- Add validation

### Step 3: State Machine (3h)
- Implement state machine with transitions
- Add validation logic
- Progress calculation

### Step 4: Onboarding Service (4h)
- Implement all service methods
- Integrate with document processing
- Integrate with payment processing
- Business logic

### Step 5: API Endpoints (2h)
- Create all API endpoints
- Request/response handling
- Error handling

### Step 6: Database Migration (0.5h)
- Create migration for onboardings table

### Step 7: Tests (4h)
- State machine tests
- Service tests
- API tests

## Integration Points

**With Task 3.3 (Document Processing):**
- Upload documents via onboarding workflow
- Check document validation status
- Track document IDs in onboarding

**With Task 3.1 (Payment Processing):**
- Calculate onboarding fee
- Process payment via payment service
- Track payment ID in onboarding

**With Lead Model:**
- Associate onboarding with lead
- Update lead status on completion

## Success Criteria

- ✅ State machine with 9 states and transitions
- ✅ Onboarding service with complete workflow
- ✅ API endpoints for all operations
- ✅ Integration with document processing
- ✅ Integration with payment processing
- ✅ Database migration
- ✅ 35 tests passing

## Files Summary

**New Files (7):**
1. `AIM/src/aim/models/onboarding.py` (120 lines)
2. `AIM/src/aim/schemas/onboarding.py` (200 lines)
3. `AIM/src/aim/services/onboarding/state_machine.py` (300 lines)
4. `AIM/src/aim/services/onboarding/onboarding_service.py` (400 lines)
5. `AIM/src/aim/api/onboarding.py` (350 lines)
6. `AIM/alembic/versions/004_onboarding_table.py` (60 lines)
7. `AIM/tests/services/test_onboarding.py` (500 lines)

**Modified Files (1):**
1. `AIM/src/aim/models/__init__.py` (add Onboarding export)

**Total:** 8 files, ~1,930 lines

## Estimated Time Breakdown

- Step 1: Onboarding Model - 1.5h
- Step 2: Onboarding Schemas - 2h
- Step 3: State Machine - 3h
- Step 4: Onboarding Service - 4h
- Step 5: API Endpoints - 2h
- Step 6: Database Migration - 0.5h
- Step 7: Tests - 4h

**Total:** 17h (buffer included)
