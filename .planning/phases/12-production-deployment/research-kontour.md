# Контур.Диадок API — Research for Integration

**Date:** 2026-05-18
**Purpose:** Replace KontourClient stub with real API integration
**Researcher:** meAI (Claude Opus 4)

---

## 1. Executive Summary

Контур.Диадок provides a REST API for electronic document exchange with legally-significant signatures. The API uses **OpenID Connect** for authentication, supports both **JSON and Protocol Buffers** for serialization, and is entirely **polling-based** (no webhooks). There is **no official Python SDK** -- only C#, Java, and C++.

**Key decisions for our integration:**
- We will use **JSON** format (simpler, no protobuf compilation needed)
- We will use **Device Authorization Flow** (best fit for server-to-server integration)
- We will implement **polling via GetNewEvents (V8)** to track document status changes
- We will build our own Python client using `httpx` (same stack as our other API clients)

---

## 2. Authentication

### 2.1 Method: OpenID Connect (OAuth 2.0)

**Identity Provider:** `identity.kontur.ru`

Diadoc supports two authentication schemes:
- **OpenID Connect** (RECOMMENDED) -- industry-standard OAuth 2.0 / OIDC
- **DiadocAuth** (DEPRECATED) -- legacy, uses `Authenticate (V3)` method with login/password or certificate

We will use OpenID Connect.

### 2.2 Prerequisites

1. Register integration solution at https://www.diadoc.ru/integrations/api
2. Receive `client_id` from Diadoc manager
3. Generate `client_secret` in Integrator Cabinet (https://integrations.kontur.ru/)

### 2.3 Device Authorization Flow (Recommended for Server-to-Server)

Best fit for backend/CLI applications where no browser redirect is practical.

**Step 1 -- Request device/user codes:**
```bash
POST https://identity.kontur.ru/connect/deviceauthorization
Content-Type: application/x-www-form-urlencoded

client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
&scope=openid profile email offline_access Diadoc.PublicAPI
```

**Response:**
```json
{
    "device_code": "NGU5OWFiNjQ5YmQwNGY3YTdmZTEyNzQ3YzQ1YSA",
    "user_code": "BDWPHQPK",
    "verification_uri": "https://identity.kontur.ru/device",
    "verification_uri_complete": "https://identity.kontur.ru/device?user-code=BDWPHQPK",
    "interval": 3,
    "expires_in": 300
}
```

**Step 2 -- User authorizes:**
Open `verification_uri_complete` in browser, enter `user_code`, log in, grant permissions.

**Step 3 -- Poll for tokens (every `interval` seconds):**
```bash
POST https://identity.kontur.ru/connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
&scope=openid profile email offline_access Diadoc.PublicAPI
&device_code=DEVICE_CODE_FROM_STEP_1
```

**Success Response:**
```json
{
    "access_token": "AYjcyMzY3ZDhiNmJkNTY",
    "id_token": "eyJhbGciOifQ.ewogI3pAKfQ.ggW8hq-rvKMzqg",
    "refresh_token": "RjY2NjM5NzA2OWJjuE7c",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "openid profile email offline_access Diadoc.PublicAPI"
}
```

**Possible poll responses:**
- `authorization_pending` -- user hasn't completed yet, keep polling
- `access_denied` -- user refused
- `expired_token` -- device_code expired (5 minute lifetime)

### 2.4 Authorization Code Flow (Alternative)

For web apps with redirect capability:
1. Redirect user to `GET https://identity.kontur.ru/connect/authorize?response_type=code&client_id=...&scope=...&redirect_uri=...&nonce=...`
2. User authorizes, gets redirected back with `?code=...`
3. Exchange code for tokens: `POST /connect/token` with `grant_type=authorization_code`

**Authorization code lifetime:** 5 minutes

### 2.5 Token Refresh

```bash
POST https://identity.kontur.ru/connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
&refresh_token=YOUR_REFRESH_TOKEN
```

**Response:**
```json
{
    "access_token": "811d583cf85deb7ab67bd91b96a9a4bafb63d6a062d7dd72f81601b84c19dc40",
    "token_type": "Bearer",
    "expires_in": 86400,
    "refresh_token": "fd672752f8e9c4a8eb083fb2375b3126ae37dc69a0cf46953ef9a6e3f5a692df"
}
```

**Token lifetimes:**
| Token | Lifetime |
|-------|----------|
| Authorization code | 5 minutes |
| Device code | 300 seconds (5 minutes) |
| Initial access_token | 3600 seconds (1 hour) |
| Refreshed access_token | 86400 seconds (24 hours) |

**CRITICAL:** Must refresh before expiry, otherwise API calls fail with 401.

### 2.6 Required Scopes

| Scope | Required | Purpose |
|-------|----------|---------|
| `openid` | YES | OpenID Connect interaction |
| `profile` | YES | Basic user profile |
| `email` | YES | User email |
| `offline_access` | YES | Enables refresh_token |
| `Diadoc.PublicAPI` | YES (prod) | Production API access |
| `Diadoc.PublicAPI.Staging` | YES (staging) | Test environment access |

### 2.7 API Call Headers

Every API call requires:
```
Authorization: Bearer <access_token>
Accept: application/json; charset=utf-8
Content-Type: application/json; charset=utf-8
```

---

## 3. API Base URLs

| Environment | URL |
|-------------|-----|
| **Production** | `https://diadoc-api.kontur.ru` |
| **Staging (Test)** | `https://diadoc-api-staging.kontur.ru` |
| **Identity Provider** | `https://identity.kontur.ru` |

---

## 4. Core API Endpoints for Our Use Case

### 4.1 Get Organization Info (Box ID)

```
GET /GetMyOrganizations
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Accept: application/json
```

Returns list of organizations the authenticated user can access. Returns `BoxId` (GUID) for each organization's box. The `BoxId` is required for almost all subsequent API calls.

**Our organization:** "ООО \"АИМ Маркетинг\"", INN 7701234567

### 4.2 Get Counterparty (Recipient)

```
GET /GetCounteragents?myBoxId={{boxId}}&counteragentStatus=&afterIndexKey=
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Accept: application/json
```

Returns list of counterparties for the given box. Use this to find (or acquire) the recipient's `BoxId`.

**Alternative:** Use `GET /GetOrganizationsByInnKpp?inn={{inn}}` to look up by INN.

### 4.3 Send Document for Signature

```
POST /V3/PostMessage
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Content-Type: application/json; charset=utf-8
```

**Query params:**
- `operationId` (optional) -- idempotency key. Defaults to MD5 hash of request body.

**Request body (MessageToPost structure):**
```json
{
    "FromBoxId": "{{sender_box_id}}",
    "ToBoxId": "{{recipient_box_id}}",
    "DocumentAttachments": [{
        "SignedContent": {
            "Content": "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48RG9jdW1lbnQ+...",
            "Signature": "MIIN5QYJKoZIhvcNAQcCoIIN1jCCDdICAQExDzANBglghkgBZQMEAgEFAD...",
            "PowerOfAttorney": {
                "FullId": {
                    "RegistrationNumber": "{{registrationNumber}}",
                    "IssuerInn": "{{issuerInn}}"
                }
            }
        },
        "TypeNamedId": "nonformalized",
        "Function": "NoAdditionalInfo",
        "Version": "",
        "Comment": "Contract for signing",
        "CustomDocumentId": "AIM-CONTRACT-001",
        "Metadata": [
            {"Key": "FileName", "Value": "contract_aim_2026.pdf"}
        ]
    }]
}
```

**Key fields:**
- `SignedContent.Content`: Base64-encoded file content (XML or PDF wrapped)
- `SignedContent.Signature`: Base64-encoded electronic signature (must be generated client-side!)
- `TypeNamedId`: Document type -- `"nonformalized"` for contracts/agreements
- `CustomDocumentId`: Our internal reference ID
- Max 40 documents per message
- Single document max 70 MB

**CRITICAL:** Diadoc API does NOT generate signatures. We must:
1. Generate the signature ourselves using a crypto provider (КриптоПро CSP)
2. OR use `DssSign` to sign via Diadoc's cloud certificate service

### 4.4 Sign Document with Cloud Certificate (DSS)

If we have a cloud-based certificate in Diadoc:

```
POST /DssSign?boxId={{boxId}}&certificateThumbprint={{thumbprint}}
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Content-Type: application/json; charset=utf-8
```

**Request body (DssSignRequest):**
```json
{
    "Files": [
        {
            "Content": {"Content": "<fileBytesBase64>"},
            "FileName": "contract_aim_2026.pdf"
        }
    ]
}
```

**Response (async):**
```json
{
    "TaskId": "2fd45887-138e-4e08-aeb2-bcd55bf0dd85"
}
```

**Poll for result:**
```
GET /DssSignResult?boxId={{boxId}}&taskId={{taskId}}
```

**Note:** `certificateThumbprint` is optional. If omitted, Diadoc uses the non-expired cloud certificate with the longest validity period.

**DssSign V2** adds support for Госключ (government key service).

**Alternative signing methods:**
- `SignWithTestSignature = true` -- for testing only (no real legal force)
- `PrepareDocumentsToSign` -- prepares documents for signing, returns what needs to be signed

### 4.5 Check Document Status

```
GET /V3/GetDocument?boxId={{boxId}}&messageId={{messageId}}&entityId={{entityId}}
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Accept: application/json; charset=utf-8
```

**Response (Document structure) -- key fields:**
```json
{
    "MessageId": "guid",
    "EntityId": "guid",
    "DocumentType": "Nonformalized",
    "TypeNamedId": "nonformalized",
    "FileName": "contract_aim_2026.pdf",
    "DocumentNumber": "1",
    "DocumentDate": "2026-05-18",
    "DocumentDirection": "Outbound",
    "IsTest": false,
    "IsDeleted": false,
    "CreationTimestampTicks": 639046580000000000,
    "SendTimestampTicks": 639046581000000000,
    "DeliveryTimestampTicks": 639046582000000000,
    "SenderSignatureStatus": "SenderSignatureCheckedAndValid",
    "ProxySignatureStatus": "ProxySignatureStatusNone",
    "DocflowStatus": {
        "PrimaryStatus": {
            "Severity": "Info",
            "StatusText": "Документооборот завершен"
        }
    },
    "RecipientReceiptMetadata": {
        "ReceiptStatus": "Finished"
    },
    "RecipientResponseStatus": "RecipientResponseStatusNotAcceptable",
    "RevocationStatus": "RevocationStatusNone",
    "Content": {
        "Size": 6658,
        "Data": "<base64>"
    }
}
```

**Important status fields:**
- `DocflowStatus.PrimaryStatus.StatusText` -- human-readable status
- `SenderSignatureStatus` -- signature validation status
- `RecipientReceiptMetadata.ReceiptStatus` -- receipt/delivery status
- `RecipientResponseStatus` -- whether signed/declined

**Content size limit:** If document content exceeds 1,048,576 bytes, use `GET /V4/GetEntityContent` to download separately.

### 4.6 Poll for Document Events (Status Changes)

Two methods available:

#### Option A: GetNewEvents (V8) -- Recommended
```
GET /V8/GetNewEvents?boxId={{boxId}}&afterIndexKey={{indexKey}}&limit=100
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Accept: application/json; charset=utf-8
```

**Query parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `boxId` | Yes | Box GUID |
| `afterIndexKey` | No | Cursor for pagination (URL-encoded) |
| `afterEventId` | Deprecated | Replaced by `afterIndexKey` |
| `departmentId` | No | Filter by department |
| `messageType` | No | Comma-separated: `Draft`, `Letter`, `Template` |
| `typeNamedId` | No | Filter by document type |
| `documentDirection` | No | Comma-separated: `Inbound`, `Outbound`, `Internal` |
| `timestampFromTicks` | No | Start time in ticks |
| `timestampToTicks` | No | End time in ticks |
| `counteragentBoxId` | No | Filter by counterparty |
| `orderBy` | No | `Ascending` (default) or `Descending` |
| `limit` | No | 1-500, default 500 |

**Response (BoxEventList):**
- `Events` array (max 500 per page)
- `TotalCount` -- total matching events
- Each event has `IndexKey` for pagination

**Event types in response:**
1. **Message events** -- new messages in the box
2. **Patch events** -- updates to existing messages (signatures, status changes)

**Key tracking fields in events:**
- `SenderSignatureStatus` -- e.g., `"SenderSignatureUnchecked"` → `"SenderSignatureCheckedAndValid"`
- `DocflowStatus.PrimaryStatus` -- e.g., `"Ожидается извещение о получении"` → `"Документооборот завершен"`
- `RecipientReceiptMetadata.ReceiptStatus` -- `"WaitingForReceipt"` → `"Finished"`
- `RecipientResponseStatus` -- `"WaitingForRecipientSignature"` → signed/declined
- `MessageIsDelivered` -- patch flag indicating delivery

**Pagination:** Store `BoxEvent.IndexKey` and pass as `afterIndexKey` for next page.

#### Option B: GetDocflowEvents (V4)
```
POST /V4/GetDocflowEvents?boxId={{boxId}}
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Content-Type: application/json; charset=utf-8
```

**Request body:**
```json
{
    "MessageTypes": ["Letter"],
    "DocumentDirections": ["Outbound"],
    "Filter": {
        "FromTimestamp": {"Ticks": 639046500000000000},
        "ToTimestamp": {"Ticks": 639046600000000000}
    },
    "AfterIndexKey": "",
    "limit": 100,
    "PopulateDocuments": true,
    "PopulatePreviousDocumentStates": false
}
```

**Key feature:** Can include document state at event time (`PopulateDocuments`) and at previous event (`PopulatePreviousDocumentStates`), enabling diff comparison.

### 4.7 Download Signed Document

**Method 1 -- via GetDocument (if content < 1 MB):**
```
GET /V3/GetDocument?boxId={{boxId}}&messageId={{messageId}}&entityId={{entityId}}
```
The `Content.Data` field contains Base64-encoded file bytes.

**Method 2 -- via GetEntityContent (for large files):**
```
GET /V4/GetEntityContent?boxId={{boxId}}&messageId={{messageId}}&entityId={{entityId}}
```

### 4.8 Get Signature Certificate / Signature Info

```
GET /GetSignatureInfo?boxId={{boxId}}&messageId={{messageId}}&entityId={{entityId}}
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Accept: application/json; charset=utf-8
```

Returns information about all signatures on the document, including signer certificates.

### 4.9 Download Print Form (Signed Document with Stamp)

```
GET /GeneratePrintForm?boxId={{boxId}}&messageId={{messageId}}&entityId={{entityId}}
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Accept: application/json; charset=utf-8
```

Generates a printable PDF with signature marks/stamps.

### 4.10 Get Counteragent Certificates

```
GET /V2/GetCounteragentCertificates?myBoxId={{boxId}}&counteragentBoxId={{counteragentBoxId}}
Host: diadoc-api.kontur.ru
Authorization: Bearer {{access_token}}
Accept: application/json; charset=utf-8
```

Returns list of valid certificates for a counterparty. Used to verify they can legally sign.

---

## 5. Webhooks / Callbacks

**Диадок does NOT have webhooks.** The API is entirely polling-based. There is no webhook configuration, no HMAC signature verification, and no push notification mechanism.

**How to detect status changes:**
1. Store the last `IndexKey` from `GetNewEvents (V8)`
2. Periodically poll `GetNewEvents (V8)` with `afterIndexKey`
3. Process new events and update local document status

**Email notifications** are available via the subscriptions API:
- `POST /UpdateSubscriptions` -- subscribe user to email notifications
- `GET /GetSubscriptions` -- get current subscriptions
- Available notification types: `NewIncomingDocuments`, `CounteragentSignatures`, `CounteragentSignatureDenials`, etc.

**Our polling strategy:**
- Check `GetNewEvents` every 30-60 seconds during active signing flows
- Use exponential backoff if no changes detected (up to 5 minutes)
- For immediate status checks, call `GetDocument (V3)` directly by ID

---

## 6. Signature Types

### 6.1 Russian Legal Classification (ФЗ-63 "Об электронной подписи")

| Type | Russian Name | Use Case | API Behavior |
|------|-------------|----------|--------------|
| **Simple** | Простая электронная подпись (ПЭП) | < 100,000 RUB | SMS/email confirmation (not handled by Diadoc directly) |
| **Enhanced Unqualified** | Усиленная неквалифицированная (УНЭП) | 100,000 - 600,000 RUB | Certificate-based, generated by crypto provider |
| **Enhanced Qualified** | Усиленная квалифицированная (КЭП) | > 600,000 RUB | Qualified certificate from accredited CA, issued by ФНС |

### 6.2 How Diadoc API Handles Signatures

Diadoc works primarily with **qualified electronic signatures (КЭП)** -- certificates issued by accredited certification authorities.

**Key points:**
- Diadoc does NOT generate signatures. The client must generate them using a crypto provider.
- `DssSign` allows signing with cloud-based certificates stored in Diadoc (carrier-less).
- `SignWithTestSignature = true` flag is for TESTING ONLY -- no legal force.
- The API distinguishes `SenderSignatureStatus` values:
  - `SenderSignatureUnchecked` -- not yet validated
  - `SenderSignatureCheckedAndValid` -- validated and valid
  - `SenderSignatureCheckedAndInvalid` -- validated and invalid

**For our implementation:**
- We will use the same legal classification as before (Simple <100k, Enhanced 100k-600k, Qualified >600k)
- This determines which type of signature the recipient must use
- The API call itself is the same regardless -- we send the document with appropriate metadata
- For qualified signatures, we need to ensure the recipient has a valid КЭП certificate
- We use `GetCounteragentCertificates` to verify this before sending

---

## 7. Data Formats

### 7.1 JSON (We will use this)

Set these headers on every request:
```
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
```

**Limitation:** Only the latest data structure versions are available in JSON. Older versions require protobuf.

### 7.2 Protocol Buffers (Default, not for us)

- Official protobuf `.proto` files define the API contract
- SDKs (C#, Java, C++) bundle the compiled protobuf stubs
- For Python, we'd need to compile `.proto` files with `protoc` and use `protobuf` library
- Backward compatibility advantage over JSON

**Decision:** Use JSON. Simpler integration, no protobuf compilation step needed.

---

## 8. Rate Limits & Constraints

| Constraint | Value |
|------------|-------|
| Maximum throughput (official) | 200 RPS |
| Recommended max load | 100 RPS |
| Recommended parallel threads | 4 |
| Documents per message | 40 |
| Single document size in message | 70 MB |
| File size on document shelf | 400 MB |
| Single shelf fragment | 512 KB |
| Shelf file retention | 7 days |
| Entity content response limit | 1,048,576 bytes |

**Authentication token:** Use a single token across all threads/requests.

**Error codes to handle:**
| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | -- |
| 204 | In progress with Retry-After | Wait and retry |
| 400 | Bad request | Fix request format |
| 401 | Unauthorized | Refresh access_token |
| 402 | API subscription expired | Alert finance/operations |
| 403 | Forbidden | Check box access permissions |
| 404 | Not found | Check document/message IDs |
| 405 | Wrong method | Fix HTTP method |
| 409 | Conflict / Duplicate | Use idempotency key |
| 500 | Internal server error | Retry with backoff |

---

## 9. Python Integration Strategy

### 9.1 No Official Python SDK

Diadoc provides SDKs for:
- **C#** -- `diadocsdk-csharp` (40 stars, actively maintained)
- **Java** -- `diadocsdk-java` (23 stars, last release March 2026)
- **C++** -- `diadocsdk-cpp` (8 stars, last updated 2024)

There is NO official Python SDK. Community projects found:
- **glsv/diadoc-api** (PHP wrapper) -- reference for architecture patterns
- **diadoc/diadocsdk-1c-docs** (Python, 29 stars) -- only for 1C documentation generation, NOT an API client

### 9.2 Our Python Client Design

We will build our own client using `httpx` (consistent with our existing `api_clients/` pattern):

```python
# AIM/src/aim/services/contracts/kontour_client.py

class KontourClient:
    def __init__(self, client_id, client_secret, box_id, base_url, identity_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.box_id = box_id
        self.base_url = base_url
        self.identity_url = identity_url
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def authenticate_device_flow(self):
        """Device authorization flow"""

    async def _refresh_access_token(self):
        """Refresh expired token"""

    async def _ensure_authenticated(self):
        """Check token validity, refresh if needed"""

    async def send_for_signature(self, document, signers, signature_type):
        """
        1. Upload document to shelf (ShelfUpload)
        2. Sign with DssSign (cloud certificate)
        3. Send via PostMessage (V3)
        4. Returns messageId + entityId
        """

    async def get_document_status(self, document_id):
        """
        Calls GetDocument (V3) for immediate status
        """

    async def download_signed_document(self, document_id):
        """
        Uses GetDocument (V3) or GetEntityContent (V4) for large files
        """

    async def get_signature_certificate(self, document_id):
        """
        Calls GetSignatureInfo, returns certificate data
        """

    async def poll_events(self, after_index_key=None):
        """
        Calls GetNewEvents (V8) for status change polling
        """
```

### 9.3 Reuse Existing Resilience Patterns

Apply the same patterns from our API clients layer:
- Circuit breaker (`pybreaker`)
- Retry with exponential backoff (`tenacity`)
- Token bucket rate limiting (`aiolimiter`)
- Response caching (`aiocache`)
- Structured logging (`structlog`)
- Metrics (`prometheus-client`)

---

## 10. Implementation Notes for the Current Interface

### 10.1 Mapping Current Interface to Diadoc API

| Current Method | Diadoc API Calls Needed |
|---------------|------------------------|
| `send_for_signature(document_path, recipient_email, recipient_name, recipient_inn, signature_type, message)` | 1. `GetMyOrganizations` (get boxId) 2. `GetOrganizationsByInnKpp` (find/get recipient boxId) 3. `ShelfUpload` (upload document) 4. `DssSign` (sign with cloud cert, poll result) 5. `PostMessage (V3)` (send to recipient) |
| `get_document_status(document_id)` | `GetDocument (V3)` with `messageId` + `entityId` |
| `download_signed_document(document_id)` | `GetDocument (V3)` or `GetEntityContent (V4)` for large files |
| `get_signature_certificate(document_id)` | `GetSignatureInfo` + `GeneratePrintForm` |
| `cancel_signature_request(document_id, reason)` | `PostMessagePatch (V4)` with revocation request |
| `resend_notification(document_id)` | Not directly available -- use `UpdateSubscriptions` or resend entire message |
| `get_organization_info()` | `GetMyOrganizations` + `GetOrganization` |

### 10.2 Document ID Mapping

Our `document_id` maps to a composite key:
- `document_id = f"{messageId}:{entityId}"` (separated by colon)
- We store both in our database for individual API calls

### 10.3 No Webhooks -- Replace KontourWebhookHandler

Since Diadoc has no webhooks, the `KontourWebhookHandler` class should be replaced with:
- **Polling service** that calls `GetNewEvents (V8)` on a schedule
- **Status change callbacks** triggered by the polling service

### 10.4 Signature Type Handling

The `signature_type` parameter (SIMPLE/ENHANCED/QUALIFIED) affects:
- What metadata we include in the document
- Whether we verify recipient has valid КЭП certificate via `GetCounteragentCertificates`
- It does NOT change the API endpoint or method used

---

## 11. Staging/Testing

### 11.1 Test Environment

- **API Base:** `https://diadoc-api-staging.kontur.ru`
- **OIDC Scope:** `Diadoc.PublicAPI.Staging`
- **Test organization:** Diadoc provides test organizations for development
- **Test signature:** Use `SignWithTestSignature: true` (no real certificate needed)

### 11.2 Quick Start Test Flow

1. Register as integrator
2. Get `client_id` and `client_secret`
3. Authenticate via Device Flow
4. `GetMyOrganizations` -- get test box ID
5. `GetCounteragents` -- get test counterparty box ID
6. Prepare document with `SignWithTestSignature: true`
7. `POST /V3/PostMessage` -- send document
8. `GET /V3/GetDocument` -- check status
9. `GET /V8/GetNewEvents` -- monitor events

---

## 12. Configuration

### 12.1 Environment Variables

```bash
# Контур.Диадок Integration
DIADOC_CLIENT_ID=your_client_id_here
DIADOC_CLIENT_SECRET=your_client_secret_here
DIADOC_BOX_ID=your_organization_box_id
DIADOC_BASE_URL=https://diadoc-api.kontur.ru
DIADOC_STAGING_URL=https://diadoc-api-staging.kontur.ru
DIADOC_IDENTITY_URL=https://identity.kontur.ru
DIADOC_USE_STAGING=false
DIADOC_CERTIFICATE_THUMBPRINT=  # optional, for DssSign
```

### 12.2 Settings Model (Pydantic)

```python
class DiadocSettings(BaseSettings):
    diadoc_client_id: str
    diadoc_client_secret: str
    diadoc_box_id: str
    diadoc_base_url: str = "https://diadoc-api.kontur.ru"
    diadoc_identity_url: str = "https://identity.kontur.ru"
    diadoc_use_staging: bool = False
    diadoc_certificate_thumbprint: Optional[str] = None
    diadoc_poll_interval_seconds: int = 30
    diadoc_max_poll_interval_seconds: int = 300

    model_config = SettingsConfigDict(env_prefix="DIADOC_")
```

---

## 13. Key API Reference Pages

| Topic | URL |
|-------|-----|
| Main Documentation | https://developer.kontur.ru/doc/diadoc-api/ |
| Authentication | https://developer.kontur.ru/docs/diadoc-api/authentication.html |
| Integration Guide | https://developer.kontur.ru/docs/diadoc-api/howtostart/integration.html |
| Quick Start | https://developer.kontur.ru/docs/diadoc-api/howtostart/quickstart.html |
| Technical Specs | https://developer.kontur.ru/docs/diadoc-api/techinfo.html |
| Method Catalog | https://developer.kontur.ru/docs/diadoc-api/api-catalog/index.html |
| PostMessage (V3) | https://developer.kontur.ru/docs/diadoc-api/http/PostMessage.html |
| GetDocument (V3) | https://developer.kontur.ru/docs/diadoc-api/http/GetDocument.html |
| DssSign | https://developer.kontur.ru/docs/diadoc-api/http/DssSign.html |
| GetNewEvents (V8) | https://developer.kontur.ru/docs/diadoc-api/http/GetNewEvents_V8.html |
| OpenAPI Spec | https://developer.kontur.ru/doc/diadoc.api |
| SDK & Examples | https://diadoc.kontur.ru/sdk/ |
| Integration Samples | https://github.com/diadoc/integration-samples |
| Registration | https://www.diadoc.ru/integrations/api |

---

## 14. What to Delete (DocuSign)

The DocuSign client (554 lines) at:
```
AIM/src/aim/services/onboarding/docusign_client.py
AIM/tests/services/onboarding/test_docusign.py
```

These files should be DELETED. DocuSign is:
- Not applicable in Russian jurisdiction
- Replaced entirely by Контур.Диадок
- Only existed as a reference stub

---

## 15. Summary: What We Know vs What We Need

**CONFIRMED:**
- [x] Authentication: OpenID Connect with Device Authorization Flow
- [x] API base URL: `https://diadoc-api.kontur.ru`
- [x] REST endpoints for sending (PostMessage V3), status (GetDocument V3), events (GetNewEvents V8)
- [x] Download via GetEntityContent (V4)
- [x] Signature certificates via GetSignatureInfo
- [x] No webhooks -- polling only (GetNewEvents V8)
- [x] Rate limits: 200 RPS max, 4 parallel threads, 40 docs per message
- [x] No official Python SDK -- build our own with httpx
- [x] JSON format supported with proper headers
- [x] Signature types map to legal requirements, not API parameters

**NEEDS REAL CREDENTIALS TO TEST:**
- [ ] Register integration at https://www.diadoc.ru/integrations/api to get `client_id`
- [ ] Generate `client_secret` in Integrator Cabinet
- [ ] Find our organization's BoxId via GetMyOrganizations
- [ ] Test sending to test counterparty
- [ ] Validate polling logic with real events
- [ ] Test DssSign with cloud certificate
- [ ] Verify document status transitions in practice
- [ ] Confirm exact response fields for error scenarios

**OPEN QUESTIONS FOR DIADOC SUPPORT:**
1. Is there a sandbox/test environment with pre-configured test counterparties?
2. Do we need КриптоПро CSP installed for client-side signing, or can we use only DssSign (cloud certs)?
3. What is the exact document content format for non-formalized documents (PDF wrapped in XML, or raw PDF)?
4. Are there any IP whitelisting requirements for API access?
5. What is the API subscription cost for our use case (low volume: ~50-100 docs/month)?
