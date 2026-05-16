import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentUpload } from "@/components/onboarding/DocumentUpload";

// Mock fetch
global.fetch = jest.fn();

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = jest.fn(() => "mock-url");
global.URL.revokeObjectURL = jest.fn();

describe("DocumentUpload", () => {
  const mockOnDataExtracted = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  describe("Rendering", () => {
    it("should render upload area", () => {
      render(<DocumentUpload />);

      expect(screen.getByText(/Загрузите документы/)).toBeInTheDocument();
      expect(
        screen.getByText(/PNG, JPG до 10MB \(можно несколько\)/)
      ).toBeInTheDocument();
    });

    it("should apply custom className", () => {
      const { container } = render(
        <DocumentUpload className="custom-class" />
      );

      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass("custom-class");
    });
  });

  describe("File Selection", () => {
    it("should accept image files", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);

      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });
    });

    it("should accept multiple files", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const files = [
        new File(["image1"], "test1.jpg", { type: "image/jpeg" }),
        new File(["image2"], "test2.png", { type: "image/png" }),
      ];
      const input = screen.getByLabelText(/Загрузите документы/);

      await user.upload(input, files);

      await waitFor(() => {
        expect(screen.getByText("test1.jpg")).toBeInTheDocument();
        expect(screen.getByText("test2.png")).toBeInTheDocument();
      });
    });

    it("should reject non-image files", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload onError={mockOnError} />);

      const file = new File(["pdf"], "test.pdf", { type: "application/pdf" });
      const input = screen.getByLabelText(/Загрузите документы/) as HTMLInputElement;

      await user.upload(input, file);

      // Wait for error to be called
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith(
          "Файл test.pdf не является изображением"
        );
      });
    });

    it("should reject files larger than 10MB", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload onError={mockOnError} />);

      // Create 11MB file
      const largeFile = new File([new ArrayBuffer(11 * 1024 * 1024)], "large.jpg", {
        type: "image/jpeg",
      });
      const input = screen.getByLabelText(/Загрузите документы/);

      await user.upload(input, largeFile);

      expect(mockOnError).toHaveBeenCalledWith(
        "Файл large.jpg слишком большой (макс. 10MB)"
      );
    });
  });

  describe("Document Type Selection", () => {
    it("should allow changing document type", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);

      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });

      const select = screen.getByRole("combobox");
      await user.selectOptions(select, "medical_license");

      expect(select).toHaveValue("medical_license");
    });

    it("should show all document type options", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);

      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });

      expect(screen.getByText("Медицинская лицензия")).toBeInTheDocument();
      expect(screen.getByText("Сертификат")).toBeInTheDocument();
      expect(screen.getByText("Договор")).toBeInTheDocument();
      expect(
        screen.getByText("Свидетельство о регистрации")
      ).toBeInTheDocument();
      expect(screen.getByText("Другое")).toBeInTheDocument();
    });
  });

  describe("Document Removal", () => {
    it("should allow removing documents", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);

      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });

      const removeButton = screen.getByRole("button", { name: "" });
      await user.click(removeButton);

      await waitFor(() => {
        expect(screen.queryByText("test.jpg")).not.toBeInTheDocument();
      });
    });
  });

  describe("Document Processing", () => {
    it("should process documents successfully", async () => {
      const user = userEvent.setup();
      render(
        <DocumentUpload onDataExtracted={mockOnDataExtracted} />
      );

      // Upload file
      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);
      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });

      // Mock successful API response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          results: [
            {
              success: true,
              data: {
                clinicName: "Стоматология Дента Плюс",
                inn: "7707083893",
                confidence: 85,
                extractedFields: ["clinicName", "inn"],
                warnings: [],
              },
              processingTime: 1000,
            },
          ],
          merged: {
            clinicName: "Стоматология Дента Плюс",
            inn: "7707083893",
            confidence: 85,
            extractedFields: ["clinicName", "inn"],
            warnings: [],
          },
          totalProcessingTime: 1000,
          totalTokensUsed: 1500,
        }),
      });

      // Click process button
      const processButton = screen.getByRole("button", {
        name: /Обработать документы/,
      });
      await user.click(processButton);

      // Wait for processing
      await waitFor(() => {
        expect(screen.getByText(/Обработка документов\.\.\./)).toBeInTheDocument();
      });

      // Wait for success
      await waitFor(() => {
        expect(screen.getByText(/Данные извлечены/)).toBeInTheDocument();
      });

      expect(mockOnDataExtracted).toHaveBeenCalledWith({
        clinicName: "Стоматология Дента Плюс",
        inn: "7707083893",
        confidence: 85,
        extractedFields: ["clinicName", "inn"],
        warnings: [],
      });
    });

    it("should show error on processing failure", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload onError={mockOnError} />);

      // Upload file
      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);
      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });

      // Mock API error
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
      });

      // Click process button
      const processButton = screen.getByRole("button", {
        name: /Обработать документы/,
      });
      await user.click(processButton);

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith("Ошибка обработки документов");
      });
    });

    it("should show error when no documents uploaded", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload onError={mockOnError} />);

      // Try to process without uploading
      const processButton = screen.queryByRole("button", {
        name: /Обработать документы/,
      });

      expect(processButton).not.toBeInTheDocument();
    });

    it("should disable processing during upload", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      // Upload file
      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);
      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });

      // Mock slow API response
      (global.fetch as jest.Mock).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({
                    success: true,
                    results: [],
                    merged: { clinicName: "", confidence: 0, extractedFields: [], warnings: [] },
                  }),
                }),
              100
            )
          )
      );

      // Click process button
      const processButton = screen.getByRole("button", {
        name: /Обработать документы/,
      });
      await user.click(processButton);

      // Button should be disabled during processing
      expect(processButton).toBeDisabled();
    });
  });

  describe("Merged Data Display", () => {
    it("should display extracted clinic data", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      // Upload file
      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);
      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });

      // Mock API response with full data
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          results: [{
            success: true,
            data: {
              clinicName: "Стоматология Дента Плюс",
              confidence: 90,
              extractedFields: ["clinicName", "inn", "ogrn"],
              warnings: [],
            }
          }],
          merged: {
            clinicName: "Стоматология Дента Плюс",
            inn: "7707083893",
            ogrn: "1027700132195",
            legalAddress: "г. Москва, ул. Ленина, д. 1",
            specialties: ["Стоматология", "Ортопедия"],
            licenseNumber: "ЛО-77-01-012345",
            directorName: "Иванов Иван Иванович",
            confidence: 90,
            extractedFields: ["clinicName", "inn", "ogrn", "legalAddress", "specialties", "licenseNumber", "directorName"],
            warnings: [],
          },
        }),
      });

      // Process
      const processButton = screen.getByRole("button", {
        name: /Обработать документы/,
      });
      await user.click(processButton);

      // Wait for data display
      await waitFor(() => {
        expect(screen.getByText(/Данные извлечены/)).toBeInTheDocument();
      });

      expect(screen.getByText("Стоматология Дента Плюс")).toBeInTheDocument();
      expect(screen.getByText("7707083893")).toBeInTheDocument();
      expect(screen.getByText("1027700132195")).toBeInTheDocument();
      expect(screen.getByText("г. Москва, ул. Ленина, д. 1")).toBeInTheDocument();
      expect(screen.getByText("Стоматология, Ортопедия")).toBeInTheDocument();
      expect(screen.getByText("ЛО-77-01-012345")).toBeInTheDocument();
      expect(screen.getByText("Иванов Иван Иванович")).toBeInTheDocument();
    });

    it("should display warnings", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      // Upload file
      const file = new File(["image"], "test.jpg", { type: "image/jpeg" });
      const input = screen.getByLabelText(/Загрузите документы/);
      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("test.jpg")).toBeInTheDocument();
      });

      // Mock API response with warnings
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          results: [{
            success: true,
            data: {
              clinicName: "Клиника",
              confidence: 50,
              extractedFields: ["clinicName"],
              warnings: ["Invalid INN format", "Missing license number"],
            }
          }],
          merged: {
            clinicName: "Клиника",
            confidence: 50,
            extractedFields: ["clinicName"],
            warnings: ["Invalid INN format", "Missing license number"],
          },
        }),
      });

      // Process
      const processButton = screen.getByRole("button", {
        name: /Обработать документы/,
      });
      await user.click(processButton);

      // Wait for warnings
      await waitFor(() => {
        expect(screen.getByText(/Предупреждения:/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Invalid INN format/)).toBeInTheDocument();
      expect(screen.getByText(/Missing license number/)).toBeInTheDocument();
    });
  });

  describe("File Size Display", () => {
    it("should display file size in KB", async () => {
      const user = userEvent.setup();
      render(<DocumentUpload />);

      // Create 5KB file
      const file = new File([new ArrayBuffer(5 * 1024)], "test.jpg", {
        type: "image/jpeg",
      });
      const input = screen.getByLabelText(/Загрузите документы/);

      await user.upload(input, file);

      await waitFor(() => {
        expect(screen.getByText("5 KB")).toBeInTheDocument();
      });
    });
  });
});
