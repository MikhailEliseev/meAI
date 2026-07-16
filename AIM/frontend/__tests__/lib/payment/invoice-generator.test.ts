import {
  generateInvoice,
  generateInvoiceNumber,
  calculateVAT,
  calculateInvoiceTotals,
  formatCurrency,
  formatDate,
  markInvoiceAsSent,
  markInvoiceAsPaid,
  getInvoice,
  getCustomerInvoices,
} from "@/lib/payment/invoice-generator";
import type {
  InvoiceGenerateRequest,
  InvoiceItem,
} from "@/lib/payment/invoice-generator";

describe("Invoice Generator", () => {
  const mockItems: InvoiceItem[] = [
    {
      description: "AI-маркетинг для медицинских клиник (месяц)",
      quantity: 1,
      unitPrice: 150000,
      vatRate: 20,
      total: 150000,
    },
  ];

  const mockCustomer = {
    name: "Стоматология Дента Плюс",
    email: "ivan@dentaplus.ru",
    phone: "+79991234567",
    inn: "7707083893",
  };

  describe("generateInvoiceNumber", () => {
    it("should generate invoice number with correct format", () => {
      const number = generateInvoiceNumber(1);
      expect(number).toMatch(/^AIM-\d{4}-\d{3}$/);
      expect(number).toContain("2026");
    });

    it("should pad sequence number with zeros", () => {
      expect(generateInvoiceNumber(1)).toContain("-001");
      expect(generateInvoiceNumber(42)).toContain("-042");
      expect(generateInvoiceNumber(999)).toContain("-999");
    });
  });

  describe("calculateVAT", () => {
    it("should calculate VAT correctly", () => {
      expect(calculateVAT(100000, 20)).toBe(20000);
      expect(calculateVAT(100000, 10)).toBe(10000);
      expect(calculateVAT(100000, 0)).toBe(0);
    });

    it("should round VAT amount", () => {
      expect(calculateVAT(100001, 20)).toBe(20000);
    });
  });

  describe("calculateInvoiceTotals", () => {
    it("should calculate totals correctly", () => {
      const items: InvoiceItem[] = [
        {
          description: "Service 1",
          quantity: 1,
          unitPrice: 100000,
          vatRate: 20,
          total: 100000,
        },
        {
          description: "Service 2",
          quantity: 2,
          unitPrice: 50000,
          vatRate: 20,
          total: 100000,
        },
      ];

      const totals = calculateInvoiceTotals(items);

      expect(totals.subtotal).toBe(200000);
      expect(totals.vatAmount).toBe(40000);
      expect(totals.total).toBe(240000);
    });

    it("should handle mixed VAT rates", () => {
      const items: InvoiceItem[] = [
        {
          description: "Service with 20% VAT",
          quantity: 1,
          unitPrice: 100000,
          vatRate: 20,
          total: 100000,
        },
        {
          description: "Service with 10% VAT",
          quantity: 1,
          unitPrice: 100000,
          vatRate: 10,
          total: 100000,
        },
      ];

      const totals = calculateInvoiceTotals(items);

      expect(totals.subtotal).toBe(200000);
      expect(totals.vatAmount).toBe(30000); // 20K + 10K
      expect(totals.total).toBe(230000);
    });
  });

  describe("generateInvoice", () => {
    it("should generate invoice with all fields", async () => {
      const request: InvoiceGenerateRequest = {
        customer: mockCustomer,
        items: mockItems,
        dueInDays: 7,
        notes: "Test invoice",
      };

      const invoice = await generateInvoice(request);

      expect(invoice.id).toBeDefined();
      expect(invoice.number).toMatch(/^AIM-\d{4}-\d{3}$/);
      expect(invoice.date).toBeDefined();
      expect(invoice.dueDate).toBeDefined();
      expect(invoice.customer).toEqual(mockCustomer);
      expect(invoice.items).toEqual(mockItems);
      expect(invoice.subtotal).toBe(150000);
      expect(invoice.vatAmount).toBe(30000);
      expect(invoice.total).toBe(180000);
      expect(invoice.currency).toBe("RUB");
      expect(invoice.status).toBe("draft");
      expect(invoice.notes).toBe("Test invoice");
    });

    it("should use default due date (7 days)", async () => {
      const request: InvoiceGenerateRequest = {
        customer: mockCustomer,
        items: mockItems,
      };

      const invoice = await generateInvoice(request);

      const dueDate = new Date(invoice.dueDate);
      const expectedDueDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

      // Allow 1 second difference for test execution time
      expect(Math.abs(dueDate.getTime() - expectedDueDate.getTime())).toBeLessThan(
        1000
      );
    });

    it("should use custom due date", async () => {
      const request: InvoiceGenerateRequest = {
        customer: mockCustomer,
        items: mockItems,
        dueInDays: 14,
      };

      const invoice = await generateInvoice(request);

      const dueDate = new Date(invoice.dueDate);
      const expectedDueDate = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000);

      expect(Math.abs(dueDate.getTime() - expectedDueDate.getTime())).toBeLessThan(
        1000
      );
    });
  });

  describe("markInvoiceAsSent", () => {
    it("should mark invoice as sent", async () => {
      const invoice = await markInvoiceAsSent("test-invoice-id");

      expect(invoice.status).toBe("sent");
      expect(invoice.id).toBe("test-invoice-id");
    });
  });

  describe("markInvoiceAsPaid", () => {
    it("should mark invoice as paid", async () => {
      const invoice = await markInvoiceAsPaid("test-invoice-id", "bank_card");

      expect(invoice.status).toBe("paid");
      expect(invoice.paymentMethod).toBe("bank_card");
      expect(invoice.paidAt).toBeDefined();
    });
  });

  describe("getInvoice", () => {
    it("should get invoice by ID", async () => {
      const invoice = await getInvoice("test-invoice-id");

      expect(invoice).not.toBeNull();
      expect(invoice?.id).toBe("test-invoice-id");
      expect(invoice?.status).toBe("sent");
    });
  });

  describe("getCustomerInvoices", () => {
    it("should get invoices for customer", async () => {
      const invoices = await getCustomerInvoices("test@example.com");

      expect(invoices).toHaveLength(2);
      expect(invoices[0].status).toBe("paid");
      expect(invoices[1].status).toBe("sent");
    });
  });

  describe("formatCurrency", () => {
    it("should format currency in Russian format", () => {
      // Use regex to handle both regular and non-breaking spaces
      expect(formatCurrency(150000)).toMatch(/150\s000\s₽/);
      expect(formatCurrency(1500000)).toMatch(/1\s500\s000\s₽/);
      expect(formatCurrency(0)).toMatch(/0\s₽/);
    });
  });

  describe("formatDate", () => {
    it("should format date in Russian format", () => {
      const date = new Date("2026-05-16T12:00:00Z");
      const formatted = formatDate(date.toISOString());

      // Check that date contains expected parts
      expect(formatted).toContain("16");
      expect(formatted).toContain("2026");
      expect(formatted).toMatch(/\d{1,2}/); // day
      expect(formatted).toMatch(/\d{4}/); // year
    });
  });
});
