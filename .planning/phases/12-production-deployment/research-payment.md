# YooKassa Python SDK Research

**Date:** 2026-05-18
**Purpose:** Replace HelcimClient stub with real YooKassa integration
**Researcher:** meAI Architect

---

## Executive Summary

YooKassa (formerly Yandex.Checkout) is the primary Russian payment processor. Three Python libraries are available. **We recommend `async_yookassa`** as the primary choice because it is async-native (httpx-based) and matches our stack. The official `yookassa` SDK is synchronous-only and would require `run_in_executor` wrappers. `aioyookassa` is a feature-rich alternative with built-in webhook server support.

### Recommendation

| Library | Async | HTTP Client | Snippets | Rating |
|---------|-------|-------------|----------|--------|
| **async_yookassa** (prodreams) | Yes | httpx | 38 | 87.4 benchmark |
| aioyookassa (masasibata) | Yes | httpx | 575 | 88.5 benchmark |
| yookassa (official) | No | requests | 8 | N/A (sync) |

**Primary pick:** `async_yookassa` — clean async API, matches our httpx stack, simpler than aioyookassa.
**Fallback:** `aioyookassa` if we need built-in webhook server or more comprehensive features.
**Last resort:** `yookassa` official SDK (wrap sync calls in `asyncio.to_thread`).

---

## 1. Installation

### async_yookassa (recommended)
```bash
pip install async-yookassa
# or
pip install async_yookassa
```

Dependencies: httpx, pydantic

### aioyookassa (alternative)
```bash
pip install aioyookassa
```

Dependencies: httpx, pydantic, aiohttp (for webhook server)

### yookassa official (sync)
```bash
pip install yookassa
```

Dependencies: requests, python-dateutil

---

## 2. Configuration

All libraries require the same credentials:
- **shopId** (also called account_id): Found in YooKassa Merchant Profile
- **Secret Key**: Generated in Integration → API Keys section

### Test Environment
- Demo store credentials work out of the box
- No real money is transferred
- Test cards available for bank card payments
- Test shopId: `54401`, test secret: `test_Fh8hUAVVBGUGbjmlzba6TB0iyUbos_lueTHE-axOwM0`
- Test card: `5555 5555 5555 4444`, expiry `12/25+`, CVV `000`

### async_yookassa config
```python
from async_yookassa import YooKassaClient

async with YooKassaClient(
    account_id="123456",          # Your shopId
    secret_key="live_xxxxxx",     # Your secret key
    timeout=60,                   # Optional, default 30s
) as client:
    me = await client.me.get_me()
    print(f"Shop: {me.name}, Status: {me.status}")
```

### aioyookassa config
```python
from aioyookassa import YooKassa

async with YooKassa(
    api_key="test_xxxxxx",        # Secret key
    shop_id=12345,                # Your shopId (int)
) as client:
    # use client.payments, client.refunds, etc.
```

### Official yookassa config (sync)
```python
from yookassa import Configuration

Configuration.configure("123456", "test_xxxxxx")
# or
Configuration.account_id = "123456"
Configuration.secret_key = "test_xxxxxx"
```

---

## 3. Creating a Payment (async_yookassa)

### Auto-capture (one-step payment)
```python
from async_yookassa import YooKassaClient
from async_yookassa.models.payment import (
    PaymentRequest, Amount, RedirectConfirmationRequest,
)

async with YooKassaClient(account_id="123456", secret_key="test_xxx") as client:
    request = PaymentRequest(
        amount=Amount(value="1500.00", currency="RUB"),
        confirmation=RedirectConfirmationRequest(
            type="redirect",
            return_url="https://iamaim.ru/payment/success"
        ),
        description="Order #12345 - Medical marketing consultation",
        capture=True,  # Auto-capture (one-step)
        metadata={"order_id": "12345", "user_id": "user_789"}
    )
    payment = await client.payment.create(request)
    
    print(f"Payment ID: {payment.id}")
    print(f"Status: {payment.status}")        # pending
    print(f"Confirmation URL: {payment.confirmation.confirmation_url}")
```

### Two-step payment (authorize, then capture)
```python
# Step 1: Authorize (hold funds)
request = PaymentRequest(
    amount=Amount(value="1500.00", currency="RUB"),
    confirmation=RedirectConfirmationRequest(
        type="redirect",
        return_url="https://iamaim.ru/payment/success"
    ),
    capture=False,  # Two-step - hold funds
    description="Order #12345"
)
payment = await client.payment.create(request)
# Status: pending → waiting_for_capture (after user pays)

# Step 2: Capture (charge funds)
captured = await client.payment.capture(payment.id)
# Status: succeeded
```

### Creating payment in aioyookassa
```python
from aioyookassa import YooKassa
from aioyookassa.types.payment import Money, Confirmation
from aioyookassa.types.enum import PaymentStatus, ConfirmationType, Currency
from aioyookassa.types.params import CreatePaymentParams

async with YooKassa(api_key="test_xxx", shop_id=12345) as client:
    params = CreatePaymentParams(
        amount=Money(value=1000.00, currency=Currency.RUB),
        confirmation=Confirmation(
            type=ConfirmationType.REDIRECT,
            return_url="https://example.com/success"
        ),
        description="Оплата заказа #12345",
        metadata={"order_id": "12345"}
    )
    payment = await client.payments.create_payment(params)
    print(f"Payment ID: {payment.id}")
    print(f"URL for payment: {payment.confirmation.url}")
```

### Creating payment in official yookassa (sync)
```python
from yookassa import Payment

payment = Payment.create({
    "amount": {"value": "1000.00", "currency": "RUB"},
    "confirmation": {
        "type": "redirect",
        "return_url": "https://iamaim.ru/payment/success"
    },
    "capture": True,
    "description": "Order #12345",
    "metadata": {"order_id": "12345"}
})
print(payment.id, payment.status, payment.confirmation.confirmation_url)
```

---

## 4. Checking Payment Status

### async_yookassa
```python
# Get by ID
payment = await client.payment.find_one("2be00000-0000-0000-0000-000000000001")
print(f"Status: {payment.status}")       # pending | waiting_for_capture | succeeded | canceled
print(f"Amount: {payment.amount.value} {payment.amount.currency}")
print(f"Paid: {payment.paid}")
print(f"Created: {payment.created_at}")
if payment.payment_method:
    print(f"Method: {payment.payment_method.type}")  # bank_card, yoo_money, sbp, etc.

# List with filters
from async_yookassa.models.payment import PaymentListOptions

payments = await client.payment.list(
    PaymentListOptions(
        limit=20,
        status="succeeded",
        created_at_gte="2024-01-01T00:00:00Z",
    )
)
for p in payments.items:
    print(f"{p.id}: {p.status} - {p.amount.value} RUB")
```

### aioyookassa
```python
# Get by ID
payment = await client.payments.get_payment("payment_id")
print(f"Status: {payment.status}")

# List
from aioyookassa.types.params import GetPaymentsParams
from aioyookassa.types.enum import PaymentStatus

params = GetPaymentsParams(
    status=PaymentStatus.SUCCEEDED,
    limit=5
)
payments = await client.payments.get_payments(params)
```

### Official yookassa (sync)
```python
from yookassa import Payment

# Get by ID
payment = Payment.find_one("payment_id")

# List
payments = Payment.list({
    "limit": 20,
    "status": "succeeded",
})
```

---

## 5. Processing Refunds

### async_yookassa (full refund)
```python
from async_yookassa.models.refund import RefundRequest, Amount

refund = await client.refund.create(
    RefundRequest(
        payment_id="2be00000-0000-0000-0000-000000000001",
        amount=Amount(value="1500.00", currency="RUB"),
        description="Customer requested refund"
    )
)
print(f"Refund ID: {refund.id}")
print(f"Status: {refund.status}")  # succeeded
```

### async_yookassa (partial refund)
```python
refund = await client.refund.create(
    RefundRequest(
        payment_id="2be00000-0000-0000-0000-000000000001",
        amount=Amount(value="500.00", currency="RUB"),  # Partial
        description="Partial refund for overcharge"
    )
)
```

### async_yookassa (get refund info)
```python
# Get specific refund
refund = await client.refund.find_one("refund_id")
print(f"Refund {refund.id}: {refund.status}")

# List refunds
from async_yookassa.models.refund import RefundListOptions

refunds = await client.refund.list(
    RefundListOptions(limit=20, status="succeeded")
)
```

### aioyookassa
```python
from aioyookassa.types.params import CreateRefundParams
from aioyookassa.types.models import PaymentAmount
from aioyookassa.types.enum import Currency

params = CreateRefundParams(
    payment_id="payment_id",
    amount=PaymentAmount(value=500.00, currency=Currency.RUB),
    description="Возврат части средств"
)
refund = await client.refunds.create_refund(params)
```

### Official yookassa (sync)
```python
from yookassa import Refund

refund = Refund.create({
    "payment_id": "24e89cb0-000f-5000-9000-1de77fa0d6df",
    "description": "Refund reason",
    "amount": {
        "value": "9000.00",
        "currency": "RUB"
    }
})

# Get info
refund = Refund.find_one("refund_id")

# List
refunds = Refund.list({"limit": 20, "payment_id": "..."})
```

**IMPORTANT:** Refunds are only available for 3 years after payment creation. Not all payment methods support refunds (e.g., cash payments via terminals).

---

## 6. Webhook Handling

### Payment Lifecycle & Webhook Events

```
pending → waiting_for_capture → succeeded
  ↓                               ↓
canceled                      refund.succeeded
```

Available webhook events:

| Event | Description |
|-------|-------------|
| `payment.waiting_for_capture` | Funds authorized, ready to capture |
| `payment.succeeded` | Payment completed successfully |
| `payment.canceled` | Payment was canceled |
| `refund.succeeded` | Refund processed successfully |

**CRITICAL:** YooKassa will resend the webhook every 10 minutes for 24 hours if it does NOT receive HTTP 200. Any other response code (including 400, 500) is considered failure and triggers retry.

### IP Validation
YooKassa provides IPs you should validate against:
- YooKassa sends notifications from specific IP ranges
- Use `SecurityHelper().is_ip_trusted(ip)` in official SDK
- For async libraries, implement your own or use the built-in validator

### async_yookassa webhook management
```python
from async_yookassa.models.webhook import WebhookRequest, WebhookEvent

# Create webhook
webhook = await client.webhook.create(
    WebhookRequest(
        event=WebhookEvent.PAYMENT_SUCCEEDED,
        url="https://iamaim.ru/api/webhooks/yookassa/payment"
    )
)

# List webhooks
webhooks = await client.webhook.list()

# Delete webhook
await client.webhook.delete(webhook.id)
```

### aioyookassa webhook handling (built-in server)
```python
from aioyookassa.contrib.webhook_server import WebhookServer
from aioyookassa.core.webhook_handler import WebhookHandler
from aioyookassa.types.enum import WebhookEvent
from aioyookassa.types.payment import Payment

handler = WebhookHandler()

@handler.register_callback(WebhookEvent.PAYMENT_SUCCEEDED)
async def on_payment_succeeded(payment: Payment):
    print(f"Payment {payment.id} completed successfully")
    # Update database, trigger fulfillment

@handler.register_callback(WebhookEvent.PAYMENT_CANCELED)
async def on_payment_canceled(payment: Payment):
    print(f"Payment {payment.id} was canceled")

@handler.register_callback(WebhookEvent.REFUND_SUCCEEDED)
async def on_refund_succeeded(refund):
    print(f"Refund {refund.id} completed")

server = WebhookServer(handler=handler)
server.run(host="0.0.0.0", port=8080)
```

### aioyookassa webhook integration with existing FastAPI app
```python
from aiohttp import web
from aioyookassa.core.webhook_handler import WebhookHandler
from aioyookassa.types.enum import WebhookEvent

handler = WebhookHandler()

@handler.register_callback(WebhookEvent.PAYMENT_SUCCEEDED)
async def on_payment_succeeded(payment):
    await process_payment(payment)

async def webhook_endpoint(request):
    # Validate IP
    if not handler.validator.is_allowed(request.remote):
        raise web.HTTPForbidden()

    # Parse and handle notification
    data = await request.json()
    notification = handler.parse_notification(data)
    await handler.handle_notification(notification)
    return web.Response(status=200)  # CRITICAL: must return 200!
```

### Official yookassa webhook handling (sync)
```python
import json
from yookassa import Configuration, Payment
from yookassa.domain.notification import (
    WebhookNotificationFactory,
    WebhookNotificationEventType,
)
from yookassa.domain.common.security_helper import SecurityHelper

def my_webhook_handler(request):
    # Validate IP
    ip = get_client_ip(request)
    if not SecurityHelper().is_ip_trusted(ip):
        return HttpResponse(status=400)

    event_json = json.loads(request.body)
    try:
        notification = WebhookNotificationFactory().create(event_json)
        response_object = notification.object

        if notification.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            payment_id = response_object.id
            status = response_object.status
            # Your business logic here

        elif notification.event == WebhookNotificationEventType.PAYMENT_WAITING_FOR_CAPTURE:
            payment_id = response_object.id
            # Capture if needed: Payment.capture(payment_id)

        elif notification.event == WebhookNotificationEventType.PAYMENT_CANCELED:
            payment_id = response_object.id
            # Handle cancellation

        elif notification.event == WebhookNotificationEventType.REFUND_SUCCEEDED:
            refund_id = response_object.id
            payment_id = response_object.payment_id
            # Handle refund notification

    except Exception:
        return HttpResponse(status=400)  # YooKassa will retry

    return HttpResponse(status=200)  # MUST return 200!
```

### Notification JSON Format (from YooKassa)
```json
{
  "type": "notification",
  "event": "payment.succeeded",
  "object": {
    "id": "22d6d597-000f-5000-9000-145f6df21d6f",
    "status": "succeeded",
    "paid": true,
    "amount": {
      "value": "2.00",
      "currency": "RUB"
    },
    "created_at": "2018-07-10T14:27:54.691Z",
    "description": "Order No. 72",
    "metadata": {"order_id": "72"},
    "payment_method": {
      "type": "bank_card",
      "id": "22d6d597-000f-5000-9000-145f6df21d6f",
      "saved": false,
      "card": {
        "first6": "555555",
        "last4": "4444",
        "expiry_month": "07",
        "expiry_year": "2021",
        "card_type": "MasterCard",
        "issuer_country": "RU",
        "issuer_name": "Sberbank"
      },
      "title": "Bank card *4444"
    },
    "refundable": true,
    "test": false
  }
}
```

---

## 7. Error Handling

### async_yookassa exceptions
```python
from async_yookassa.exceptions import (
    APIError,               # General API error
    BadRequestError,        # Invalid request / validation
    UnauthorizedError,      # Wrong credentials (401)
    ForbiddenError,         # Insufficient permissions (403)
    NotFoundError,          # Resource not found (404)
    TooManyRequestsError,   # Rate limited (429)
    ResponseProcessingError # YooKassa processing, retry later
)

async def handle_payment():
    try:
        payment = await client.payment.create(request)
    except BadRequestError as e:
        # Validation error - check request params
        logger.error(f"Invalid payment request: {e}")
    except UnauthorizedError as e:
        # Wrong shop_id or secret_key
        logger.error(f"Authentication failed: {e}")
    except ForbiddenError as e:
        # Insufficient shop permissions
        logger.error(f"Access denied: {e}")
    except NotFoundError as e:
        # Payment not found
        logger.error(f"Not found: {e}")
    except TooManyRequestsError as e:
        # Rate limited - implement exponential backoff
        logger.warning(f"Rate limited: {e}")
    except ResponseProcessingError as e:
        # YooKassa is still processing - retry
        logger.info(f"Still processing, retry later: {e}")
    except APIError as e:
        # Catch-all
        logger.error(f"API error: {e}")
```

### aioyookassa exceptions
```python
from aioyookassa.exceptions import APIError, NotFound

try:
    payment = await client.payments.create_payment(params)
except NotFound:
    print("Payment not found")
except APIError as e:
    print(f"API error: {e}")
```

### Common API Error Codes (from YooKassa docs)

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 400 | Invalid request | Check parameters |
| 401 | Authentication error | Check shopId & secretKey |
| 403 | Forbidden | Check permissions |
| 404 | Not found | Resource doesn't exist |
| 429 | Too many requests | Implement backoff |
| 500 | Internal error | YooKassa-side, retry |

### Payment statuses
| Status | Meaning |
|--------|---------|
| `pending` | Created, waiting for user to pay |
| `waiting_for_capture` | Funds authorized, needs capture |
| `succeeded` | Payment completed |
| `canceled` | Payment was canceled |

---

## 8. Gotchas & Important Notes

### 8.1 No Card Data in Our Backend
**CRITICAL:** YooKassa handles card data on their side via redirect/widget. We do NOT store, transmit, or process card numbers, expiry dates, or CVVs. This is a fundamental architecture change from the HelcimClient stub:

- **HelcimClient (old):** `process_payment(card_number, card_expiry, card_cvv, ...)`
- **YooKassaClient (new):** `create_payment(amount, currency, return_url, metadata, ...)` — returns `confirmation_url`, user pays on YooKassa's page

**Impact on PaymentService:**
- Remove `card_number`, `card_expiry`, `card_cvv` from `PaymentRequest` schema
- Add `return_url` field to `PaymentRequest`
- Payment status tracking via webhooks instead of instant "completed"
- `PaymentStatus` enum needs `PENDING` (waiting for user payment)
- Payment is NOT completed immediately — flow becomes async

### 8.2 Idempotency Key
Every create-payment request MUST include a unique `Idempotence-Key` header. This prevents duplicate charges on retry. The SDKs handle this automatically. If you send the same key twice, YooKassa returns the original payment instead of creating a duplicate.

### 8.3 Test Mode
- Demo store is ALWAYS available in Merchant Profile
- Test payments: no real money transferred
- Use test card `5555 5555 5555 4444`, any future expiry, any CVV
- `payment.test` field will be `true` for demo store payments
- Never ship real products from demo store
- Use SEPARATE webhook URL for test notifications

### 8.4 54-FZ Receipt Data
Russian law requires sending receipt data to tax authorities. YooKassa can handle this:
```python
# Payment with receipt data
PaymentRequest(
    amount=Amount(value="1500.00", currency="RUB"),
    confirmation=...,
    receipt={
        "customer": {
            "full_name": "Ivanov Ivan",
            "email": "customer@email.ru",
            "phone": "79211234567",
        },
        "items": [
            {
                "description": "Medical marketing consultation",
                "quantity": "1.00",
                "amount": {"value": "1500.00", "currency": "RUB"},
                "vat_code": "1",  # Without VAT for simplified tax
                "payment_mode": "full_payment",
                "payment_subject": "service"
            }
        ]
    }
)
```
This is mandatory for production. For Phase 12, we can implement it.

### 8.5 Supported Payment Methods
YooKassa supports: bank cards (Visa, MC, Mir), YooMoney wallet, SberPay, SBP (Fast Payment System), Tinkoff, installment plans. Availability depends on your shop settings.

### 8.6 Sync vs Async Considerations
The official `yookassa` SDK is synchronous (uses `requests`). If we must use it, we wrap it:
```python
import asyncio
from yookassa import Payment

async def create_payment_async(data):
    return await asyncio.to_thread(Payment.create, data)
```
This works but is less clean than `async_yookassa` which is natively async with httpx.

### 8.7 Webhook Retry Logic
YooKassa retries webhooks for 24 hours with increasing intervals:
- First retry: ~10 minutes
- Then: ~1 hour
- Max: 24 hours
- Only HTTP 200 stops the retries
- Webhook URL MUST be HTTPS in production

### 8.8 Cancellation Time Sensitivity
- Bank card payments: cancellation is instant
- YooMoney wallet: instant
- SBP (Fast Payments): may take up to 24 hours
- Once `payment.canceled` webhook arrives, the cancellation is final

### 8.9 Environment Variables Needed
```bash
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=test_xxxxxx  # or live_xxxxxx for production
YOOKASSA_TEST_MODE=true           # true for demo store
YOOKASSA_RETURN_URL=https://iamaim.ru/payment/callback
YOOKASSA_WEBHOOK_URL=https://iamaim.ru/api/webhooks/yookassa
```

---

## 9. Migration Plan: HelcimClient → YooKassaClient

### Interface Changes

**Old interface (HelcimClient.stub):**
```python
class HelcimClient:
    async def process_payment(
        self, amount, currency, card_number, card_expiry, card_cvv,
        customer_name, customer_email, customer_phone=None, metadata=None
    ) -> dict  # Returns: success, transaction_id, status, amount, etc.
    
    async def check_payment_status(self, transaction_id) -> dict
    
    async def refund_payment(self, transaction_id, amount=None, reason="") -> dict
    
    async def close(self)
```

**New interface (YooKassaClient):**
```python
class YooKassaClient:
    async def create_payment(
        self, amount: float, currency: str, return_url: str,
        description: str = "", metadata: dict = None,
        capture: bool = True,
        receipt: dict = None,  # For 54-FZ
    ) -> dict  # Returns: payment_id, status, confirmation_url, created_at
    
    async def get_payment(self, payment_id: str) -> dict
        # Returns: payment_id, status, amount, paid, payment_method, etc.
    
    async def capture_payment(self, payment_id: str, amount: float = None) -> dict
        # For two-step payments
    
    async def cancel_payment(self, payment_id: str) -> dict
    
    async def create_refund(
        self, payment_id: str, amount: float = None, reason: str = ""
    ) -> dict  # Returns: refund_id, status, refunded_amount
    
    async def get_refund(self, refund_id: str) -> dict
    
    async def close(self)
```

### PaymentService Changes Required
1. `PaymentRequest` schema: remove card fields, add `return_url`
2. `PaymentStatus` enum: add `PENDING` (waiting for user payment on YooKassa page)
3. `create_payment()`: return `confirmation_url` for redirect
4. Add `handle_webhook(notification)` method to process YooKassa callbacks
5. Add webhook endpoint in FastAPI (`POST /api/webhooks/yookassa`)
6. Payment is no longer instantly "completed" — user must pay first, then webhook confirms

### New Payment Flow
```
1. POST /api/payments        → Create PaymentRequest
2. PaymentService.create_payment()  → YooKassaClient.create_payment()
3. YooKassa returns  → confirmation_url + payment_id (status: pending)
4. Frontend redirects → user to confirmation_url
5. User pays on       → YooKassa page
6. YooKassa sends     → webhook to our /api/webhooks/yookassa
7. We update DB        → status: succeeded
8. We trigger          → fulfillment (email, document generation, etc.)
```

---

## 10. Files to Create / Modify

### New Files
```
AIM/src/aim/services/payment/yookassa_client.py   # YooKassaClient implementation
AIM/src/aim/api/webhooks.py                       # Webhook endpoint handler
AIM/tests/services/payment/test_yookassa_client.py # Unit tests
```

### Modified Files
```
AIM/src/aim/services/payment/__init__.py           # Export YooKassaClient
AIM/src/aim/services/payment/payment_service.py     # Update to use YooKassaClient
AIM/src/aim/schemas/payment.py                     # Update PaymentRequest, PaymentStatus
AIM/src/aim/api/leads.py                           # Add webhook route (or separate file)
AIM/requirements.txt                               # Add async-yookassa
AIM/.env.example                                    # Add YooKassa vars
```

### Deprecated Files (can remove or archive)
```
AIM/src/aim/services/payment/helcim_client.py       # Remove stub
AIM/tests/services/payment/test_helcim_stub.py      # Remove stub tests
```

---

## 11. References

- **Official yookassa-sdk-python:** https://github.com/yoomoney/yookassa-sdk-python
- **async_yookassa:** https://github.com/prodreams/async_yookassa (or `pip install async-yookassa`)
- **aioyookassa:** https://github.com/masasibata/aioyookassa
- **Official API Docs:** https://yookassa.ru/developers/api
- **Testing Guide:** https://yookassa.ru/developers/payment-acceptance/testing-and-going-live/testing
- **Webhook Docs:** https://yookassa.ru/developers/using-api/webhooks
- **Test Environment (public):** `shopId=54401`, `secret=test_Fh8hUAVVBGUGbjmlzba6TB0iyUbos_lueTHE-axOwM0`
