import { NextRequest, NextResponse } from "next/server";
import { getDocumentProcessor } from "@/lib/ai/document-processor";
import type { DocumentType } from "@/lib/ai/document-processor";

/**
 * POST /api/documents/process
 *
 * Process uploaded document and extract clinic data
 *
 * Body:
 * {
 *   imageData: string (base64),
 *   documentType: "medical_license" | "certificate" | "contract" | "registration" | "other",
 *   mimeType?: string (default: "image/jpeg")
 * }
 *
 * Response:
 * {
 *   success: boolean,
 *   data?: ClinicData,
 *   error?: string,
 *   processingTime: number,
 *   tokensUsed?: number
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { imageData, documentType, mimeType } = body;

    // Validate input
    if (!imageData) {
      return NextResponse.json(
        { success: false, error: "Missing imageData" },
        { status: 400 }
      );
    }

    if (!documentType) {
      return NextResponse.json(
        { success: false, error: "Missing documentType" },
        { status: 400 }
      );
    }

    const validTypes: DocumentType[] = [
      "medical_license",
      "certificate",
      "contract",
      "registration",
      "other",
    ];

    if (!validTypes.includes(documentType)) {
      return NextResponse.json(
        {
          success: false,
          error: `Invalid documentType. Must be one of: ${validTypes.join(", ")}`,
        },
        { status: 400 }
      );
    }

    // Process document
    const processor = getDocumentProcessor();
    const result = await processor.processDocument(
      imageData,
      documentType,
      mimeType || "image/jpeg"
    );

    return NextResponse.json(result);
  } catch (error) {
    console.error("Document processing error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
        processingTime: 0,
      },
      { status: 500 }
    );
  }
}

/**
 * POST /api/documents/process-batch
 *
 * Process multiple documents and merge results
 *
 * Body:
 * {
 *   documents: Array<{
 *     imageData: string,
 *     documentType: DocumentType,
 *     mimeType?: string
 *   }>
 * }
 *
 * Response:
 * {
 *   success: boolean,
 *   results: DocumentProcessingResult[],
 *   merged: ClinicData,
 *   totalProcessingTime: number,
 *   totalTokensUsed: number
 * }
 */
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    const { documents } = body;

    // Validate input
    if (!documents || !Array.isArray(documents) || documents.length === 0) {
      return NextResponse.json(
        { success: false, error: "Missing or empty documents array" },
        { status: 400 }
      );
    }

    if (documents.length > 10) {
      return NextResponse.json(
        { success: false, error: "Maximum 10 documents per batch" },
        { status: 400 }
      );
    }

    // Process all documents
    const processor = getDocumentProcessor();
    const results = await processor.processDocuments(documents);

    // Merge results
    const merged = processor.mergeDocumentData(results);

    // Calculate totals
    const totalProcessingTime = results.reduce(
      (sum, r) => sum + r.processingTime,
      0
    );
    const totalTokensUsed = results.reduce(
      (sum, r) => sum + (r.tokensUsed || 0),
      0
    );

    return NextResponse.json({
      success: true,
      results,
      merged,
      totalProcessingTime,
      totalTokensUsed,
    });
  } catch (error) {
    console.error("Batch processing error:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
