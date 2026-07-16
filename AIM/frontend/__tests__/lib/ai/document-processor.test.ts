import { DocumentProcessor } from "@/lib/ai/document-processor";
import type {
  DocumentType,
  ClinicData,
  DocumentProcessingResult,
} from "@/lib/ai/document-processor";

// Mock Anthropic SDK
const mockCreate = jest.fn();

jest.mock("@anthropic-ai/sdk", () => {
  return {
    __esModule: true,
    default: jest.fn().mockImplementation(() => ({
      messages: {
        create: mockCreate,
      },
    })),
  };
});

describe("DocumentProcessor", () => {
  let processor: DocumentProcessor;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    mockCreate.mockClear();

    // Create processor with mock API key
    processor = new DocumentProcessor("test-api-key");
  });

  describe("processDocument", () => {
    it("should extract clinic data from medical license", async () => {
      // Mock Claude API response
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "Стоматология Дента Плюс",
              legalName: 'ООО "Дента Плюс"',
              inn: "7707083893",
              ogrn: "1027700132195",
              kpp: "770701001",
              legalAddress: "г. Москва, ул. Ленина, д. 1",
              actualAddress: "г. Москва, ул. Ленина, д. 1",
              city: "Москва",
              region: "Москва",
              specialties: ["Стоматология", "Ортопедия"],
              licenseNumber: "ЛО-77-01-012345",
              licenseIssueDate: "2020-01-15",
              licenseExpiryDate: "2025-01-15",
              licenseIssuedBy: "Департамент здравоохранения г. Москвы",
              directorName: "Иванов Иван Иванович",
              phone: "+79991234567",
              email: "info@dentaplus.ru",
              website: "https://dentaplus.ru",
            }),
          },
        ],
        usage: {
          input_tokens: 1000,
          output_tokens: 500,
        },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "medical_license"
      );

      if (!result.success) {
        console.log("Error:", result.error);
      }
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      expect(result.data?.clinicName).toBe("Стоматология Дента Плюс");
      expect(result.data?.inn).toBe("7707083893");
      expect(result.data?.ogrn).toBe("1027700132195");
      expect(result.data?.specialties).toEqual(["Стоматология", "Ортопедия"]);
      expect(result.data?.licenseNumber).toBe("ЛО-77-01-012345");
      expect(result.data?.confidence).toBeGreaterThan(80);
      expect(result.tokensUsed).toBe(1500);
    });

    it("should handle certificate document type", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "Центр Здоровье",
              inn: "7707123456",
              specialties: ["Терапия"],
              licenseNumber: null,
              licenseIssueDate: null,
              licenseExpiryDate: null,
              licenseIssuedBy: null,
              directorName: null,
              phone: null,
              email: null,
              website: null,
            }),
          },
        ],
        usage: { input_tokens: 800, output_tokens: 300 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "certificate"
      );

      expect(result.success).toBe(true);
      expect(result.data?.clinicName).toBe("Центр Здоровье");
      expect(result.data?.confidence).toBeLessThan(80); // Lower confidence due to missing fields
    });

    it("should validate INN format", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "Клиника",
              inn: "123", // Invalid INN (must be 10 or 12 digits)
            }),
          },
        ],
        usage: { input_tokens: 500, output_tokens: 200 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "other"
      );

      expect(result.success).toBe(true);
      expect(result.data?.warnings).toContain(
        "Invalid INN format: 123 (must be 10 or 12 digits)"
      );
    });

    it("should validate OGRN format", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "Клиника",
              ogrn: "12345", // Invalid OGRN (must be 13 or 15 digits)
            }),
          },
        ],
        usage: { input_tokens: 500, output_tokens: 200 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "other"
      );

      expect(result.success).toBe(true);
      expect(result.data?.warnings).toContain(
        "Invalid OGRN format: 12345 (must be 13 or 15 digits)"
      );
    });

    it("should validate KPP format", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "Клиника",
              kpp: "123", // Invalid KPP (must be 9 digits)
            }),
          },
        ],
        usage: { input_tokens: 500, output_tokens: 200 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "other"
      );

      expect(result.success).toBe(true);
      expect(result.data?.warnings).toContain(
        "Invalid KPP format: 123 (must be 9 digits)"
      );
    });

    it("should handle API errors", async () => {
      mockCreate.mockRejectedValue(new Error("API rate limit exceeded"));

      const result = await processor.processDocument(
        "base64-image-data",
        "medical_license"
      );

      expect(result.success).toBe(false);
      expect(result.error).toBe("API rate limit exceeded");
      expect(result.data).toBeUndefined();
    });

    it("should handle invalid JSON response", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: "This is not JSON",
          },
        ],
        usage: { input_tokens: 500, output_tokens: 200 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "other"
      );

      expect(result.success).toBe(false);
      expect(result.error).toContain("Failed to parse Claude response");
    });

    it("should handle missing clinic name", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "",
              inn: "7707083893",
            }),
          },
        ],
        usage: { input_tokens: 500, output_tokens: 200 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "other"
      );

      expect(result.success).toBe(true);
      expect(result.data?.warnings).toContain(
        "Clinic name is missing or too short"
      );
      expect(result.data?.confidence).toBeLessThan(50);
    });

    it("should track processing time", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "Клиника",
            }),
          },
        ],
        usage: { input_tokens: 500, output_tokens: 200 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "other"
      );

      expect(result.processingTime).toBeGreaterThanOrEqual(0);
    });
  });

  describe("processDocuments (batch)", () => {
    it("should process multiple documents", async () => {
      mockCreate
        .mockResolvedValueOnce({
          content: [
            {
              type: "text",
              text: JSON.stringify({
                clinicName: "Клиника 1",
                inn: "7707083893",
              }),
            },
          ],
          usage: { input_tokens: 500, output_tokens: 200 },
        })
        .mockResolvedValueOnce({
          content: [
            {
              type: "text",
              text: JSON.stringify({
                clinicName: "Клиника 2",
                ogrn: "1027700132195",
              }),
            },
          ],
          usage: { input_tokens: 500, output_tokens: 200 },
        });

      const results = await processor.processDocuments([
        {
          imageData: "base64-1",
          documentType: "medical_license",
        },
        {
          imageData: "base64-2",
          documentType: "certificate",
        },
      ]);

      expect(results).toHaveLength(2);
      expect(results[0].success).toBe(true);
      expect(results[1].success).toBe(true);
      expect(results[0].data?.clinicName).toBe("Клиника 1");
      expect(results[1].data?.clinicName).toBe("Клиника 2");
    });
  });

  describe("mergeDocumentData", () => {
    it("should merge data from multiple documents", () => {
      const results: DocumentProcessingResult[] = [
        {
          success: true,
          data: {
            clinicName: "Стоматология Дента Плюс",
            inn: "7707083893",
            specialties: ["Стоматология"],
            confidence: 80,
            extractedFields: ["clinicName", "inn", "specialties"],
            warnings: [],
          },
          processingTime: 1000,
        },
        {
          success: true,
          data: {
            clinicName: "Стоматология Дента Плюс",
            ogrn: "1027700132195",
            legalAddress: "г. Москва, ул. Ленина, д. 1",
            specialties: ["Ортопедия"],
            confidence: 70,
            extractedFields: ["clinicName", "ogrn", "legalAddress", "specialties"],
            warnings: ["Missing INN"],
          },
          processingTime: 1200,
        },
      ];

      const merged = processor.mergeDocumentData(results);

      expect(merged.clinicName).toBe("Стоматология Дента Плюс");
      expect(merged.inn).toBe("7707083893");
      expect(merged.ogrn).toBe("1027700132195");
      expect(merged.legalAddress).toBe("г. Москва, ул. Ленина, д. 1");
      expect(merged.specialties).toEqual(["Стоматология", "Ортопедия"]);
      expect(merged.confidence).toBe(75); // Average of 80 and 70
      expect(merged.extractedFields).toContain("clinicName");
      expect(merged.extractedFields).toContain("inn");
      expect(merged.extractedFields).toContain("ogrn");
      expect(merged.warnings).toContain("Missing INN");
    });

    it("should handle empty results", () => {
      const merged = processor.mergeDocumentData([]);

      expect(merged.clinicName).toBe("");
      expect(merged.confidence).toBe(0);
      expect(merged.extractedFields).toEqual([]);
      expect(merged.warnings).toEqual([]);
    });

    it("should skip failed results", () => {
      const results: DocumentProcessingResult[] = [
        {
          success: false,
          error: "API error",
          processingTime: 500,
        },
        {
          success: true,
          data: {
            clinicName: "Клиника",
            inn: "7707083893",
            confidence: 80,
            extractedFields: ["clinicName", "inn"],
            warnings: [],
          },
          processingTime: 1000,
        },
      ];

      const merged = processor.mergeDocumentData(results);

      expect(merged.clinicName).toBe("Клиника");
      expect(merged.inn).toBe("7707083893");
      expect(merged.confidence).toBe(80);
    });

    it("should combine unique specialties", () => {
      const results: DocumentProcessingResult[] = [
        {
          success: true,
          data: {
            clinicName: "Клиника",
            specialties: ["Стоматология", "Терапия"],
            confidence: 80,
            extractedFields: [],
            warnings: [],
          },
          processingTime: 1000,
        },
        {
          success: true,
          data: {
            clinicName: "Клиника",
            specialties: ["Терапия", "Хирургия"],
            confidence: 70,
            extractedFields: [],
            warnings: [],
          },
          processingTime: 1000,
        },
      ];

      const merged = processor.mergeDocumentData(results);

      expect(merged.specialties).toEqual([
        "Стоматология",
        "Терапия",
        "Хирургия",
      ]);
    });
  });

  describe("confidence calculation", () => {
    it("should give high confidence for complete data", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "Стоматология Дента Плюс",
              legalName: 'ООО "Дента Плюс"',
              inn: "7707083893",
              ogrn: "1027700132195",
              kpp: "770701001",
              legalAddress: "г. Москва, ул. Ленина, д. 1",
              actualAddress: "г. Москва, ул. Ленина, д. 1",
              city: "Москва",
              region: "Москва",
              specialties: ["Стоматология"],
              licenseNumber: "ЛО-77-01-012345",
              licenseIssueDate: "2020-01-15",
              licenseExpiryDate: "2025-01-15",
              licenseIssuedBy: "Департамент здравоохранения",
              directorName: "Иванов И.И.",
              phone: "+79991234567",
              email: "info@dentaplus.ru",
              website: "https://dentaplus.ru",
            }),
          },
        ],
        usage: { input_tokens: 1000, output_tokens: 500 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "medical_license"
      );

      expect(result.data?.confidence).toBeGreaterThan(90);
      expect(result.data?.extractedFields.length).toBeGreaterThan(10);
    });

    it("should give low confidence for minimal data", async () => {
      mockCreate.mockResolvedValue({
        content: [
          {
            type: "text",
            text: JSON.stringify({
              clinicName: "Клиника",
            }),
          },
        ],
        usage: { input_tokens: 500, output_tokens: 200 },
      });

      const result = await processor.processDocument(
        "base64-image-data",
        "other"
      );

      expect(result.data?.confidence).toBeLessThan(30);
      expect(result.data?.extractedFields).toEqual(["clinicName"]);
    });
  });
});
