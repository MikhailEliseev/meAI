# Task 3.3: AI Document Processing - Implementation Plan

**Date:** 2026-05-17  
**Status:** Planning  
**Estimated:** 16 hours  
**Dependencies:** Task 3.1 ✅, Task 3.2 ✅

---

## Objective

Automated document extraction and validation using AI for Russian medical clinic onboarding.

**Key Features:**
- PDF/image upload handling
- OCR with Tesseract (Russian language)
- AI extraction with Claude (clinic info, license, contacts)
- Validation rules (required fields, format checks)
- Confidence scoring

---

## Architecture

```
User uploads document (PDF/image)
  ↓
DocumentProcessor.process_document()
  ↓
1. File validation (size, format)
  ↓
2. Convert PDF to images (if needed)
  ↓
3. OCR with Tesseract (Russian)
  ↓
4. AI extraction with Claude
  ↓
5. Validate extracted data
  ↓
6. Store in database
  ↓
Return result with confidence score
```

---

## Implementation Steps

### Step 1: Install Dependencies (0.5h)

**System packages:**
```bash
# macOS
brew install tesseract tesseract-lang

# Verify Russian language support
tesseract --list-langs | grep rus
```

**Python packages:**
```bash
pip install pytesseract>=0.3.10 pdf2image>=1.16.0
```

**Update requirements.txt:**
```
pytesseract>=0.3.10
pdf2image>=1.16.0
```

---

### Step 2: Document Model (1h)

**File:** `AIM/src/aim/models/document.py` (150 lines)

**Schema:**
```python
class Document(Base):
    __tablename__ = "documents"
    
    id: str  # doc_YYYYMMDDHHMMSS_random
    lead_id: str  # FK to leads
    document_type: str  # license, inn, ogrn, contract
    file_path: str  # Storage path
    file_name: str  # Original filename
    file_size: int  # Bytes
    mime_type: str  # application/pdf, image/jpeg, etc.
    
    # Processing
    status: str  # pending, processing, completed, failed
    ocr_text: str  # Raw OCR output
    extracted_data: dict  # JSON field with parsed data
    confidence_score: float  # 0.0-1.0
    
    # Validation
    validation_status: str  # valid, invalid, needs_review
    validation_errors: list  # JSON field with error messages
    
    # Audit
    uploaded_at: datetime
    processed_at: datetime
    created_by: str
    ip_address: str
```

**Indexes:**
- lead_id
- document_type
- status
- uploaded_at

---

### Step 3: Document Schemas (1.5h)

**File:** `AIM/src/aim/schemas/document.py` (200 lines)

**Schemas:**

1. **DocumentUploadRequest:**
```python
class DocumentUploadRequest(BaseModel):
    lead_id: str
    document_type: Literal["license", "inn", "ogrn", "contract"]
    file: UploadFile
```

2. **DocumentUploadResponse:**
```python
class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    message: str
```

3. **ExtractedData:**
```python
class ExtractedData(BaseModel):
    # License
    license_number: Optional[str]
    license_date: Optional[str]
    license_issuer: Optional[str]
    
    # Clinic
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    clinic_phone: Optional[str]
    clinic_email: Optional[str]
    
    # Legal
    inn: Optional[str]
    ogrn: Optional[str]
    kpp: Optional[str]
    
    # Director
    director_name: Optional[str]
    director_position: Optional[str]
```

4. **ValidationResult:**
```python
class ValidationResult(BaseModel):
    is_valid: bool
    confidence_score: float
    errors: list[str]
    warnings: list[str]
```

5. **DocumentStatusResponse:**
```python
class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    extracted_data: Optional[ExtractedData]
    validation_result: Optional[ValidationResult]
    processed_at: Optional[datetime]
```

---

### Step 4: OCR Service (2h)

**File:** `AIM/src/aim/services/documents/ocr_service.py` (200 lines)

**Class:** `OCRService`

**Methods:**

1. **extract_text_from_image()**
```python
async def extract_text_from_image(
    self,
    image_path: str,
    lang: str = "rus"
) -> str:
    """Extract text from image using Tesseract OCR.
    
    Args:
        image_path: Path to image file
        lang: Language code (rus for Russian)
    
    Returns:
        Extracted text
    """
    # Use pytesseract with Russian language
    # Handle errors (file not found, OCR failure)
    # Return cleaned text
```

2. **extract_text_from_pdf()**
```python
async def extract_text_from_pdf(
    self,
    pdf_path: str,
    lang: str = "rus"
) -> str:
    """Extract text from PDF using OCR.
    
    Args:
        pdf_path: Path to PDF file
        lang: Language code
    
    Returns:
        Extracted text from all pages
    """
    # Convert PDF to images (pdf2image)
    # OCR each page
    # Concatenate results
    # Clean up temporary images
```

3. **preprocess_image()**
```python
def preprocess_image(self, image_path: str) -> str:
    """Preprocess image for better OCR accuracy.
    
    - Convert to grayscale
    - Increase contrast
    - Remove noise
    - Deskew if needed
    
    Returns:
        Path to preprocessed image
    """
```

**Error Handling:**
- File not found
- Unsupported format
- OCR failure
- Language model not installed

---

### Step 5: AI Extraction Service (3h)

**File:** `AIM/src/aim/services/documents/ai_extractor.py` (350 lines)

**Class:** `AIExtractor`

**Methods:**

1. **extract_from_text()**
```python
async def extract_from_text(
    self,
    text: str,
    document_type: str
) -> tuple[ExtractedData, float]:
    """Extract structured data from OCR text using Claude.
    
    Args:
        text: OCR text
        document_type: Type of document
    
    Returns:
        (extracted_data, confidence_score)
    """
    # Build prompt based on document type
    # Call Claude API with structured output
    # Parse response
    # Calculate confidence score
    # Return extracted data
```

2. **build_extraction_prompt()**
```python
def build_extraction_prompt(
    self,
    text: str,
    document_type: str
) -> str:
    """Build Claude prompt for extraction.
    
    Prompts by document type:
    - license: Extract license number, date, issuer
    - inn: Extract INN, clinic name, address
    - ogrn: Extract OGRN, legal entity info
    - contract: Extract parties, dates, terms
    """
```

3. **calculate_confidence()**
```python
def calculate_confidence(
    self,
    extracted_data: ExtractedData,
    document_type: str
) -> float:
    """Calculate confidence score based on:
    - Number of fields extracted
    - Field format validation
    - Cross-field consistency
    
    Returns:
        Score 0.0-1.0
    """
```

**Prompts:**

**License Extraction:**
```
Извлеки из текста медицинской лицензии следующие данные:
- Номер лицензии
- Дата выдачи
- Орган, выдавший лицензию
- Название клиники
- Адрес клиники
- ИНН
- ОГРН

Текст документа:
{text}

Верни результат в JSON формате.
```

**INN Extraction:**
```
Извлеки из текста свидетельства ИНН следующие данные:
- ИНН
- Название организации
- Адрес
- КПП
- ОГРН

Текст документа:
{text}

Верни результат в JSON формате.
```

---

### Step 6: Validation Service (2h)

**File:** `AIM/src/aim/services/documents/validator.py` (250 lines)

**Class:** `DocumentValidator`

**Methods:**

1. **validate_extracted_data()**
```python
async def validate_extracted_data(
    self,
    data: ExtractedData,
    document_type: str
) -> ValidationResult:
    """Validate extracted data.
    
    Checks:
    - Required fields present
    - Field formats valid
    - Cross-field consistency
    
    Returns:
        ValidationResult with errors/warnings
    """
```

2. **validate_inn()**
```python
def validate_inn(self, inn: str) -> bool:
    """Validate Russian INN format.
    
    Rules:
    - 10 or 12 digits
    - Checksum validation
    """
```

3. **validate_ogrn()**
```python
def validate_ogrn(self, ogrn: str) -> bool:
    """Validate Russian OGRN format.
    
    Rules:
    - 13 or 15 digits
    - Checksum validation
    """
```

4. **validate_license_number()**
```python
def validate_license_number(self, number: str) -> bool:
    """Validate medical license number format.
    
    Format: ЛО-XX-XX-XXXXXX
    """
```

**Validation Rules:**

**License Document:**
- Required: license_number, license_date, clinic_name
- Optional: license_issuer, clinic_address
- Format: license_number matches pattern

**INN Document:**
- Required: inn, clinic_name
- Optional: address, kpp, ogrn
- Format: INN checksum valid

**OGRN Document:**
- Required: ogrn, clinic_name
- Optional: address, inn
- Format: OGRN checksum valid

---

### Step 7: Document Processor (3h)

**File:** `AIM/src/aim/services/documents/processor.py` (400 lines)

**Class:** `DocumentProcessor`

**Methods:**

1. **process_document()**
```python
async def process_document(
    self,
    file: UploadFile,
    lead_id: str,
    document_type: str,
    client_ip: str,
    user_id: str
) -> DocumentUploadResponse:
    """Process uploaded document.
    
    Steps:
    1. Validate file (size, format)
    2. Save to storage
    3. Create document record
    4. Extract text (OCR)
    5. Extract data (AI)
    6. Validate data
    7. Update record
    8. Return result
    """
```

2. **validate_file()**
```python
def validate_file(self, file: UploadFile) -> None:
    """Validate uploaded file.
    
    Checks:
    - File size < 10MB
    - MIME type in allowed list
    - File extension valid
    
    Raises:
        ValueError if invalid
    """
```

3. **save_file()**
```python
async def save_file(
    self,
    file: UploadFile,
    document_id: str
) -> str:
    """Save file to storage.
    
    Path: data/documents/{lead_id}/{document_id}.{ext}
    
    Returns:
        File path
    """
```

4. **get_document_status()**
```python
async def get_document_status(
    self,
    document_id: str
) -> DocumentStatusResponse:
    """Get document processing status.
    
    Returns:
        Status, extracted data, validation result
    """
```

**Error Handling:**
- File too large
- Invalid format
- OCR failure
- AI extraction failure
- Validation errors
- Storage errors

---

### Step 8: API Endpoints (1.5h)

**File:** `AIM/src/aim/api/routes/documents.py` (200 lines)

**Endpoints:**

1. **POST /api/documents/upload**
```python
@router.post("/upload")
async def upload_document(
    file: UploadFile,
    lead_id: str = Form(...),
    document_type: str = Form(...),
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DocumentUploadResponse:
    """Upload and process document."""
```

2. **GET /api/documents/{document_id}/status**
```python
@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DocumentStatusResponse:
    """Get document processing status."""
```

3. **GET /api/documents/{document_id}/download**
```python
@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FileResponse:
    """Download original document."""
```

---

### Step 9: Database Migration (0.5h)

**File:** `AIM/alembic/versions/YYYYMMDD_HHMM_*_add_documents_table.py`

**Migration:**
```python
def upgrade():
    op.create_table(
        'documents',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('lead_id', sa.String(50), nullable=False),
        sa.Column('document_type', sa.String(20), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('ocr_text', sa.Text, nullable=True),
        sa.Column('extracted_data', sa.JSON, nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('validation_status', sa.String(20), nullable=True),
        sa.Column('validation_errors', sa.JSON, nullable=True),
        sa.Column('uploaded_at', sa.DateTime, nullable=False),
        sa.Column('processed_at', sa.DateTime, nullable=True),
        sa.Column('created_by', sa.String(50), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
    )
    
    op.create_index('ix_documents_lead_id', 'documents', ['lead_id'])
    op.create_index('ix_documents_document_type', 'documents', ['document_type'])
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_uploaded_at', 'documents', ['uploaded_at'])
```

---

### Step 10: Tests (4h)

**Test Files:**

1. **test_ocr_service.py** (200 lines, 8 tests):
   - test_extract_text_from_image_success
   - test_extract_text_from_pdf_success
   - test_extract_text_file_not_found
   - test_extract_text_invalid_format
   - test_preprocess_image
   - test_extract_text_russian_language
   - test_extract_text_empty_result
   - test_extract_text_ocr_failure

2. **test_ai_extractor.py** (250 lines, 10 tests):
   - test_extract_license_data
   - test_extract_inn_data
   - test_extract_ogrn_data
   - test_calculate_confidence_high
   - test_calculate_confidence_low
   - test_build_extraction_prompt_license
   - test_build_extraction_prompt_inn
   - test_extract_with_missing_fields
   - test_extract_with_invalid_format
   - test_extract_api_failure

3. **test_validator.py** (200 lines, 8 tests):
   - test_validate_inn_valid
   - test_validate_inn_invalid
   - test_validate_ogrn_valid
   - test_validate_ogrn_invalid
   - test_validate_license_number
   - test_validate_extracted_data_complete
   - test_validate_extracted_data_missing_fields
   - test_validate_cross_field_consistency

4. **test_processor.py** (300 lines, 12 tests):
   - test_process_document_success
   - test_process_document_file_too_large
   - test_process_document_invalid_format
   - test_process_document_ocr_failure
   - test_process_document_ai_failure
   - test_process_document_validation_errors
   - test_save_file_success
   - test_save_file_storage_error
   - test_get_document_status_found
   - test_get_document_status_not_found
   - test_validate_file_success
   - test_validate_file_invalid

**Total:** 38 tests

---

## File Structure

```
AIM/
├── src/aim/
│   ├── models/
│   │   └── document.py (150 lines)
│   ├── schemas/
│   │   └── document.py (200 lines)
│   ├── services/
│   │   └── documents/
│   │       ├── __init__.py (30 lines)
│   │       ├── ocr_service.py (200 lines)
│   │       ├── ai_extractor.py (350 lines)
│   │       ├── validator.py (250 lines)
│   │       └── processor.py (400 lines)
│   └── api/
│       └── routes/
│           └── documents.py (200 lines)
├── tests/
│   └── services/
│       └── documents/
│           ├── test_ocr_service.py (200 lines)
│           ├── test_ai_extractor.py (250 lines)
│           ├── test_validator.py (200 lines)
│           └── test_processor.py (300 lines)
├── alembic/
│   └── versions/
│       └── YYYYMMDD_HHMM_*_add_documents_table.py (50 lines)
└── data/
    └── documents/  # Storage directory
```

**Total:** 13 files, ~2,780 lines

---

## Testing Strategy

**Unit Tests:**
- OCR service (8 tests)
- AI extractor (10 tests)
- Validator (8 tests)
- Processor (12 tests)

**Integration Tests:**
- End-to-end document processing
- API endpoints
- Database operations

**Test Data:**
- Sample Russian documents (license, INN, OGRN)
- Mock OCR responses
- Mock Claude API responses

---

## Success Criteria

**Functional:**
- ✅ Upload PDF/image documents
- ✅ Extract text with OCR (Russian)
- ✅ Extract structured data with AI
- ✅ Validate extracted data
- ✅ Store in database
- ✅ Return confidence scores

**Performance:**
- Processing time < 60s per document
- OCR accuracy > 90% (Russian text)
- AI extraction accuracy > 85%

**Quality:**
- 38 tests passing
- Code coverage > 80%
- Error handling comprehensive

---

## Implementation Order

1. ✅ Install dependencies (0.5h)
2. ✅ Document model (1h)
3. ✅ Document schemas (1.5h)
4. ✅ OCR service (2h)
5. ✅ AI extraction service (3h)
6. ✅ Validation service (2h)
7. ✅ Document processor (3h)
8. ✅ API endpoints (1.5h)
9. ✅ Database migration (0.5h)
10. ✅ Tests (4h)

**Total:** 16 hours

---

## Next Steps

After Task 3.3 completion:
- Task 3.4: Onboarding Workflow (14h)
- Integration testing
- Documentation

