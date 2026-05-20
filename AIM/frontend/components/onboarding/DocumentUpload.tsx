"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type {
  DocumentType,
  ClinicData,
  DocumentProcessingResult,
} from "@/lib/ai/document-processor";

interface DocumentUploadProps {
  onDataExtracted?: (data: ClinicData) => void;
  onError?: (error: string) => void;
  className?: string;
}

interface UploadedDocument {
  id: string;
  file: File;
  preview: string;
  type: DocumentType;
  status: "pending" | "processing" | "success" | "error";
  result?: DocumentProcessingResult;
}

const DOCUMENT_TYPES: Array<{ value: DocumentType; label: string }> = [
  { value: "medical_license", label: "Медицинская лицензия" },
  { value: "certificate", label: "Сертификат" },
  { value: "contract", label: "Договор" },
  { value: "registration", label: "Свидетельство о регистрации" },
  { value: "other", label: "Другое" },
];

export function DocumentUpload({
  onDataExtracted,
  onError,
  className = "",
}: DocumentUploadProps) {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [mergedData, setMergedData] = useState<ClinicData | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Handle file selection
  const handleFileSelect = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      const newDocuments: UploadedDocument[] = [];

      Array.from(files).forEach((file) => {
        // Validate file type
        if (!file.type.startsWith("image/")) {
          onError?.(`Файл ${file.name} не является изображением`);
          return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
          onError?.(`Файл ${file.name} слишком большой (макс. 10MB)`);
          return;
        }

        // Create preview
        const preview = URL.createObjectURL(file);

        newDocuments.push({
          id: Math.random().toString(36).substring(7),
          file,
          preview,
          type: "other",
          status: "pending",
        });
      });

      setDocuments((prev) => [...prev, ...newDocuments]);
    },
    [onError]
  );

  // Update document type
  const updateDocumentType = useCallback(
    (id: string, type: DocumentType) => {
      setDocuments((prev) =>
        prev.map((doc) => (doc.id === id ? { ...doc, type } : doc))
      );
    },
    []
  );

  // Remove document
  const removeDocument = useCallback((id: string) => {
    setDocuments((prev) => {
      const doc = prev.find((d) => d.id === id);
      if (doc) {
        URL.revokeObjectURL(doc.preview);
      }
      return prev.filter((d) => d.id !== id);
    });
  }, []);

  // Convert file to base64
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  // Process all documents
  const processDocuments = useCallback(async () => {
    if (documents.length === 0) {
      onError?.("Загрузите хотя бы один документ");
      return;
    }

    setIsProcessing(true);

    try {
      // Convert all files to base64
      const documentsData = await Promise.all(
        documents.map(async (doc) => ({
          imageData: await fileToBase64(doc.file),
          documentType: doc.type,
          mimeType: doc.file.type,
        }))
      );

      // Update status to processing
      setDocuments((prev) =>
        prev.map((doc) => ({ ...doc, status: "processing" as const }))
      );

      // Process batch
      const response = await fetch("/api/documents/process-batch", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ documents: documentsData }),
      });

      if (!response.ok) {
        throw new Error("Ошибка обработки документов");
      }

      const data = await response.json();

      // Update documents with results
      setDocuments((prev) =>
        prev.map((doc, index) => ({
          ...doc,
          status: data.results[index].success ? "success" : "error",
          result: data.results[index],
        }))
      );

      // Set merged data
      setMergedData(data.merged);
      onDataExtracted?.(data.merged);
    } catch (error) {
      console.error("Processing error:", error);
      onError?.(
        error instanceof Error ? error.message : "Ошибка обработки документов"
      );

      // Update all to error status
      setDocuments((prev) =>
        prev.map((doc) => ({ ...doc, status: "error" as const }))
      );
    } finally {
      setIsProcessing(false);
    }
  }, [documents, onDataExtracted, onError]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Upload Area */}
      <div className="border-2 border-dashed border-border-hairline rounded-md p-8 text-center hover:border-accent transition-colors">
        <input
          type="file"
          id="document-upload"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={isProcessing}
        />
        <label
          htmlFor="document-upload"
          className="cursor-pointer block"
        >
          <div className="space-y-2">
            <svg
              className="mx-auto h-12 w-12 text-text-subtle"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div className="text-sm text-text-muted">
              <span className="font-medium text-accent hover:text-accent">
                Загрузите документы
              </span>{" "}
              или перетащите сюда
            </div>
            <p className="text-xs text-text-subtle">
              PNG, JPG до 10MB (можно несколько)
            </p>
          </div>
        </label>
      </div>

      {/* Document List */}
      <AnimatePresence>
        {documents.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {documents.map((doc) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="bg-surface-2 border border-border-hairline rounded-lg p-4 flex items-start gap-4"
              >
                {/* Preview */}
                <img
                  src={doc.preview}
                  alt={doc.file.name}
                  className="w-20 h-20 object-cover rounded"
                />

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-ink truncate">
                    {doc.file.name}
                  </p>
                  <p className="text-xs text-text-subtle">
                    {(doc.file.size / 1024).toFixed(0)} KB
                  </p>

                  {/* Type Selector */}
                  {doc.status === "pending" && (
                    <select
                      value={doc.type}
                      onChange={(e) =>
                        updateDocumentType(doc.id, e.target.value as DocumentType)
                      }
                      className="mt-2 text-sm border-border-hairline rounded-md"
                      disabled={isProcessing}
                    >
                      {DOCUMENT_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  )}

                  {/* Status */}
                  {doc.status === "processing" && (
                    <div className="mt-2 flex items-center gap-2 text-sm text-accent">
                      <div className="animate-spin h-4 w-4 border-2 border-accent border-t-transparent rounded-full" />
                      Обработка...
                    </div>
                  )}

                  {doc.status === "success" && doc.result?.data && (
                    <div className="mt-2 space-y-1">
                      <div className="flex items-center gap-2 text-sm text-semantic-success">
                        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Обработано ({doc.result.data.confidence}% уверенность)
                      </div>
                      <p className="text-xs text-text-muted">
                        Извлечено полей: {doc.result.data.extractedFields?.length || 0}
                      </p>
                    </div>
                  )}

                  {doc.status === "error" && (
                    <div className="mt-2 text-sm text-semantic-error">
                      Ошибка обработки
                    </div>
                  )}
                </div>

                {/* Remove Button */}
                {doc.status === "pending" && (
                  <button
                    onClick={() => removeDocument(doc.id)}
                    className="text-text-subtle hover:text-semantic-error"
                    disabled={isProcessing}
                  >
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                )}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Process Button */}
      {documents.length > 0 && (
        <button
          onClick={processDocuments}
          disabled={isProcessing || documents.every((d) => d.status !== "pending")}
          className="w-full bg-accent text-white py-3 px-6 rounded-lg font-medium hover:brightness-110 disabled:bg-surface-3 disabled:cursor-not-allowed transition-colors"
        >
          {isProcessing ? (
            <span className="flex items-center justify-center gap-2">
              <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
              Обработка документов...
            </span>
          ) : (
            `Обработать документы (${documents.filter((d) => d.status === "pending").length})`
          )}
        </button>
      )}

      {/* Merged Data Display */}
      {mergedData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-surface-3 border border-semantic-success/30 rounded-md p-6"
        >
          <h3 className="text-lg font-bold text-semantic-success mb-4">
            ✅ Данные извлечены ({mergedData.confidence}% уверенность)
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {mergedData.clinicName && (
              <div>
                <span className="font-medium text-text-muted">Название:</span>{" "}
                <span className="text-ink">{mergedData.clinicName}</span>
              </div>
            )}
            {mergedData.inn && (
              <div>
                <span className="font-medium text-text-muted">ИНН:</span>{" "}
                <span className="text-ink">{mergedData.inn}</span>
              </div>
            )}
            {mergedData.ogrn && (
              <div>
                <span className="font-medium text-text-muted">ОГРН:</span>{" "}
                <span className="text-ink">{mergedData.ogrn}</span>
              </div>
            )}
            {mergedData.legalAddress && (
              <div className="md:col-span-2">
                <span className="font-medium text-text-muted">Юридический адрес:</span>{" "}
                <span className="text-ink">{mergedData.legalAddress}</span>
              </div>
            )}
            {mergedData.specialties && mergedData.specialties.length > 0 && (
              <div className="md:col-span-2">
                <span className="font-medium text-text-muted">Специализации:</span>{" "}
                <span className="text-ink">{mergedData.specialties.join(", ")}</span>
              </div>
            )}
            {mergedData.licenseNumber && (
              <div>
                <span className="font-medium text-text-muted">Лицензия:</span>{" "}
                <span className="text-ink">{mergedData.licenseNumber}</span>
              </div>
            )}
            {mergedData.directorName && (
              <div>
                <span className="font-medium text-text-muted">Директор:</span>{" "}
                <span className="text-ink">{mergedData.directorName}</span>
              </div>
            )}
          </div>

          {mergedData.warnings.length > 0 && (
            <div className="mt-4 p-3 bg-surface-3 border border-amber-400/30 rounded-md">
              <p className="text-sm font-medium text-amber-400 mb-1">
                ⚠️ Предупреждения:
              </p>
              <ul className="text-xs text-amber-400/80 space-y-1">
                {mergedData.warnings.map((warning, i) => (
                  <li key={i}>• {warning}</li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
