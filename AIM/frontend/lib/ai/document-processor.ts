/**
 * AI Document Processor
 *
 * Uses Claude API to extract structured data from medical clinic documents:
 * - Medical licenses
 * - Certificates
 * - Contracts
 * - Registration documents
 *
 * Extracts:
 * - Clinic name, INN, OGRN
 * - Legal address
 * - Medical specialties
 * - License numbers and expiry dates
 * - Director name and contact info
 */

import Anthropic from "@anthropic-ai/sdk";

// Document types
export type DocumentType =
  | "medical_license"
  | "certificate"
  | "contract"
  | "registration"
  | "other";

// Extracted clinic data
export interface ClinicData {
  // Basic info
  clinicName: string;
  legalName?: string;
  inn?: string; // ИНН (10 or 12 digits)
  ogrn?: string; // ОГРН (13 or 15 digits)
  kpp?: string; // КПП (9 digits)

  // Address
  legalAddress?: string;
  actualAddress?: string;
  city?: string;
  region?: string;

  // Medical info
  specialties?: string[];
  licenseNumber?: string;
  licenseIssueDate?: string;
  licenseExpiryDate?: string;
  licenseIssuedBy?: string;

  // Contacts
  directorName?: string;
  phone?: string;
  email?: string;
  website?: string;

  // Metadata
  confidence: number; // 0-100
  extractedFields: string[]; // List of successfully extracted fields
  warnings: string[]; // Validation warnings
}

// Processing result
export interface DocumentProcessingResult {
  success: boolean;
  data?: ClinicData;
  error?: string;
  processingTime: number; // milliseconds
  tokensUsed?: number;
}

/**
 * AI Document Processor
 *
 * Extracts structured clinic data from documents using Claude API
 */
export class DocumentProcessor {
  private client: Anthropic;
  private model: string;

  constructor(apiKey?: string, model: string = "claude-3-5-sonnet-20241022") {
    this.client = new Anthropic({
      apiKey: apiKey || process.env.ANTHROPIC_API_KEY,
    });
    this.model = model;
  }

  /**
   * Process document and extract clinic data
   *
   * @param imageData - Base64 encoded image or PDF
   * @param documentType - Type of document
   * @param mimeType - MIME type (image/jpeg, image/png, application/pdf)
   * @returns Extracted clinic data
   */
  async processDocument(
    imageData: string,
    documentType: DocumentType,
    mimeType: string = "image/jpeg"
  ): Promise<DocumentProcessingResult> {
    const startTime = Date.now();

    try {
      // Build prompt based on document type
      const prompt = this.buildPrompt(documentType);

      // Call Claude API with vision
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 2000,
        messages: [
          {
            role: "user",
            content: [
              {
                type: "image",
                source: {
                  type: "base64",
                  media_type: mimeType as "image/jpeg" | "image/png" | "image/gif" | "image/webp",
                  data: imageData,
                },
              },
              {
                type: "text",
                text: prompt,
              },
            ],
          },
        ],
      });

      // Extract text from response
      const textContent = response.content.find((c) => c.type === "text");
      if (!textContent || textContent.type !== "text") {
        throw new Error("No text response from Claude API");
      }

      // Parse JSON response
      const data = this.parseResponse(textContent.text);

      // Validate extracted data
      const validation = this.validateData(data);

      const processingTime = Date.now() - startTime;

      return {
        success: true,
        data: {
          ...data,
          confidence: validation.confidence,
          extractedFields: validation.extractedFields,
          warnings: validation.warnings,
        },
        processingTime,
        tokensUsed: response.usage.input_tokens + response.usage.output_tokens,
      };
    } catch (error) {
      const processingTime = Date.now() - startTime;
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
        processingTime,
      };
    }
  }

  /**
   * Build prompt based on document type
   */
  private buildPrompt(documentType: DocumentType): string {
    const basePrompt = `Analyze this Russian medical clinic document and extract structured data.

Return ONLY a JSON object (no markdown, no explanations) with the following structure:
{
  "clinicName": "string",
  "legalName": "string or null",
  "inn": "string (10 or 12 digits) or null",
  "ogrn": "string (13 or 15 digits) or null",
  "kpp": "string (9 digits) or null",
  "legalAddress": "string or null",
  "actualAddress": "string or null",
  "city": "string or null",
  "region": "string or null",
  "specialties": ["array of strings"] or null,
  "licenseNumber": "string or null",
  "licenseIssueDate": "YYYY-MM-DD or null",
  "licenseExpiryDate": "YYYY-MM-DD or null",
  "licenseIssuedBy": "string or null",
  "directorName": "string or null",
  "phone": "string or null",
  "email": "string or null",
  "website": "string or null"
}

Rules:
- Extract ALL visible information
- Use null for missing fields
- Normalize phone numbers to +7XXXXXXXXXX format
- Convert dates to YYYY-MM-DD format
- Extract specialties as array (e.g., ["Стоматология", "Ортопедия"])
- For INN/OGRN/KPP: extract only digits, no spaces or dashes
- If text is unclear, use null instead of guessing`;

    const typeSpecificInstructions: Record<DocumentType, string> = {
      medical_license: `
This is a MEDICAL LICENSE (Лицензия на медицинскую деятельность).
Focus on:
- License number (Номер лицензии)
- Issue date (Дата выдачи)
- Expiry date (Срок действия)
- Issued by (Кем выдана)
- Medical specialties (Виды медицинской деятельности)
- Clinic name and legal details`,

      certificate: `
This is a CERTIFICATE (Сертификат).
Focus on:
- Certificate type and number
- Issue date and expiry
- Clinic name and details
- Specialties or services covered`,

      contract: `
This is a CONTRACT (Договор).
Focus on:
- Clinic name and legal details (INN, OGRN, KPP)
- Legal address
- Director name
- Contact information`,

      registration: `
This is a REGISTRATION DOCUMENT (Свидетельство о регистрации).
Focus on:
- Full legal name
- INN, OGRN, KPP
- Legal address
- Registration date
- Director name`,

      other: `
This is an UNKNOWN DOCUMENT TYPE.
Extract any visible clinic information.`,
    };

    return basePrompt + "\n" + typeSpecificInstructions[documentType];
  }

  /**
   * Parse Claude API response
   */
  private parseResponse(text: string): ClinicData {
    try {
      // Remove markdown code blocks if present
      const cleanText = text
        .replace(/```json\n?/g, "")
        .replace(/```\n?/g, "")
        .trim();

      const parsed = JSON.parse(cleanText);

      // Convert null values to undefined for optional fields
      return {
        clinicName: parsed.clinicName || "",
        legalName: parsed.legalName || undefined,
        inn: parsed.inn || undefined,
        ogrn: parsed.ogrn || undefined,
        kpp: parsed.kpp || undefined,
        legalAddress: parsed.legalAddress || undefined,
        actualAddress: parsed.actualAddress || undefined,
        city: parsed.city || undefined,
        region: parsed.region || undefined,
        specialties: parsed.specialties || undefined,
        licenseNumber: parsed.licenseNumber || undefined,
        licenseIssueDate: parsed.licenseIssueDate || undefined,
        licenseExpiryDate: parsed.licenseExpiryDate || undefined,
        licenseIssuedBy: parsed.licenseIssuedBy || undefined,
        directorName: parsed.directorName || undefined,
        phone: parsed.phone || undefined,
        email: parsed.email || undefined,
        website: parsed.website || undefined,
        confidence: 0,
        extractedFields: [],
        warnings: [],
      };
    } catch (error) {
      throw new Error(`Failed to parse Claude response: ${error}`);
    }
  }

  /**
   * Validate extracted data
   */
  private validateData(data: ClinicData): {
    confidence: number;
    extractedFields: string[];
    warnings: string[];
  } {
    const extractedFields: string[] = [];
    const warnings: string[] = [];
    let score = 0;
    let maxScore = 0;

    // Check required field: clinicName
    maxScore += 20;
    if (data.clinicName && data.clinicName.length >= 3) {
      extractedFields.push("clinicName");
      score += 20;
    } else {
      warnings.push("Clinic name is missing or too short");
    }

    // Check INN (10 or 12 digits)
    maxScore += 15;
    if (data.inn) {
      if (/^\d{10}$|^\d{12}$/.test(data.inn)) {
        extractedFields.push("inn");
        score += 15;
      } else {
        warnings.push(`Invalid INN format: ${data.inn} (must be 10 or 12 digits)`);
      }
    }

    // Check OGRN (13 or 15 digits)
    maxScore += 10;
    if (data.ogrn) {
      if (/^\d{13}$|^\d{15}$/.test(data.ogrn)) {
        extractedFields.push("ogrn");
        score += 10;
      } else {
        warnings.push(`Invalid OGRN format: ${data.ogrn} (must be 13 or 15 digits)`);
      }
    }

    // Check KPP (9 digits)
    maxScore += 5;
    if (data.kpp) {
      if (/^\d{9}$/.test(data.kpp)) {
        extractedFields.push("kpp");
        score += 5;
      } else {
        warnings.push(`Invalid KPP format: ${data.kpp} (must be 9 digits)`);
      }
    }

    // Check addresses
    maxScore += 10;
    if (data.legalAddress) {
      extractedFields.push("legalAddress");
      score += 5;
    }
    if (data.actualAddress) {
      extractedFields.push("actualAddress");
      score += 5;
    }

    // Check city and region
    maxScore += 5;
    if (data.city) {
      extractedFields.push("city");
      score += 3;
    }
    if (data.region) {
      extractedFields.push("region");
      score += 2;
    }

    // Check specialties
    maxScore += 10;
    if (data.specialties && data.specialties.length > 0) {
      extractedFields.push("specialties");
      score += 10;
    }

    // Check license info
    maxScore += 15;
    if (data.licenseNumber) {
      extractedFields.push("licenseNumber");
      score += 5;
    }
    if (data.licenseIssueDate) {
      extractedFields.push("licenseIssueDate");
      score += 5;
    }
    if (data.licenseExpiryDate) {
      extractedFields.push("licenseExpiryDate");
      score += 5;
    }

    // Check contacts
    maxScore += 10;
    if (data.directorName) {
      extractedFields.push("directorName");
      score += 3;
    }
    if (data.phone) {
      extractedFields.push("phone");
      score += 3;
    }
    if (data.email) {
      extractedFields.push("email");
      score += 2;
    }
    if (data.website) {
      extractedFields.push("website");
      score += 2;
    }

    const confidence = Math.round((score / maxScore) * 100);

    return {
      confidence,
      extractedFields,
      warnings,
    };
  }

  /**
   * Process multiple documents in batch
   */
  async processDocuments(
    documents: Array<{
      imageData: string;
      documentType: DocumentType;
      mimeType?: string;
    }>
  ): Promise<DocumentProcessingResult[]> {
    const results: DocumentProcessingResult[] = [];

    for (const doc of documents) {
      const result = await this.processDocument(
        doc.imageData,
        doc.documentType,
        doc.mimeType
      );
      results.push(result);
    }

    return results;
  }

  /**
   * Merge data from multiple documents
   *
   * Combines extracted data from multiple documents,
   * preferring higher confidence values
   */
  mergeDocumentData(results: DocumentProcessingResult[]): ClinicData {
    const merged: ClinicData = {
      clinicName: "",
      confidence: 0,
      extractedFields: [],
      warnings: [],
    };

    const allFields = new Set<string>();
    const allWarnings = new Set<string>();

    for (const result of results) {
      if (!result.success || !result.data) continue;

      const data = result.data;

      // Merge each field (prefer non-empty values)
      if (data.clinicName && !merged.clinicName) merged.clinicName = data.clinicName;
      if (data.legalName && !merged.legalName) merged.legalName = data.legalName;
      if (data.inn && !merged.inn) merged.inn = data.inn;
      if (data.ogrn && !merged.ogrn) merged.ogrn = data.ogrn;
      if (data.kpp && !merged.kpp) merged.kpp = data.kpp;
      if (data.legalAddress && !merged.legalAddress) merged.legalAddress = data.legalAddress;
      if (data.actualAddress && !merged.actualAddress) merged.actualAddress = data.actualAddress;
      if (data.city && !merged.city) merged.city = data.city;
      if (data.region && !merged.region) merged.region = data.region;
      if (data.licenseNumber && !merged.licenseNumber) merged.licenseNumber = data.licenseNumber;
      if (data.licenseIssueDate && !merged.licenseIssueDate) merged.licenseIssueDate = data.licenseIssueDate;
      if (data.licenseExpiryDate && !merged.licenseExpiryDate) merged.licenseExpiryDate = data.licenseExpiryDate;
      if (data.licenseIssuedBy && !merged.licenseIssuedBy) merged.licenseIssuedBy = data.licenseIssuedBy;
      if (data.directorName && !merged.directorName) merged.directorName = data.directorName;
      if (data.phone && !merged.phone) merged.phone = data.phone;
      if (data.email && !merged.email) merged.email = data.email;
      if (data.website && !merged.website) merged.website = data.website;

      // Merge specialties (combine unique values)
      if (data.specialties) {
        if (!merged.specialties) {
          merged.specialties = [];
        }
        merged.specialties = Array.from(
          new Set([...merged.specialties, ...data.specialties])
        );
      }

      // Collect all extracted fields and warnings
      data.extractedFields.forEach((f) => allFields.add(f));
      data.warnings.forEach((w) => allWarnings.add(w));
    }

    merged.extractedFields = Array.from(allFields);
    merged.warnings = Array.from(allWarnings);

    // Calculate average confidence
    const confidences = results
      .filter((r) => r.success && r.data)
      .map((r) => r.data!.confidence);
    merged.confidence = confidences.length > 0
      ? Math.round(confidences.reduce((a, b) => a + b, 0) / confidences.length)
      : 0;

    return merged;
  }
}

// Export singleton instance
let processorInstance: DocumentProcessor | null = null;

export function getDocumentProcessor(): DocumentProcessor {
  if (!processorInstance) {
    processorInstance = new DocumentProcessor();
  }
  return processorInstance;
}
