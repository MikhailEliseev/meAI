/**
 * Invoice Generator
 *
 * Генерация счетов для клиентов AIM Agency.
 * Поддержка российских требований к счетам.
 */

import { v4 as uuidv4 } from "uuid";

export interface InvoiceItem {
  description: string;
  quantity: number;
  unitPrice: number; // RUB
  vatRate: number; // 0, 10, or 20 (%)
  total: number; // RUB
}

export interface InvoiceCustomer {
  name: string;
  email: string;
  phone?: string;
  inn?: string; // ИНН (Tax ID)
  kpp?: string; // КПП (Tax Registration Reason Code)
  address?: string;
  bankAccount?: string;
  bankName?: string;
  bik?: string; // БИК (Bank Identification Code)
}

export interface Invoice {
  id: string;
  number: string; // Invoice number (e.g., "AIM-2026-001")
  date: string; // ISO date
  dueDate: string; // ISO date
  customer: InvoiceCustomer;
  items: InvoiceItem[];
  subtotal: number; // RUB (without VAT)
  vatAmount: number; // RUB
  total: number; // RUB (with VAT)
  currency: "RUB";
  status: "draft" | "sent" | "paid" | "overdue" | "canceled";
  paymentMethod?: string;
  paidAt?: string;
  notes?: string;
}

export interface InvoiceGenerateRequest {
  customer: InvoiceCustomer;
  items: InvoiceItem[];
  dueInDays?: number; // Default: 7 days
  notes?: string;
}

/**
 * Generate invoice number
 * Format: AIM-YYYY-NNN (e.g., AIM-2026-001)
 */
export function generateInvoiceNumber(sequenceNumber: number): string {
  const year = new Date().getFullYear();
  const paddedNumber = sequenceNumber.toString().padStart(3, "0");
  return `AIM-${year}-${paddedNumber}`;
}

/**
 * Calculate VAT amount
 */
export function calculateVAT(amount: number, vatRate: number): number {
  return Math.round((amount * vatRate) / 100);
}

/**
 * Calculate invoice totals
 */
export function calculateInvoiceTotals(items: InvoiceItem[]): {
  subtotal: number;
  vatAmount: number;
  total: number;
} {
  const subtotal = items.reduce((sum, item) => sum + item.total, 0);
  const vatAmount = items.reduce(
    (sum, item) => sum + calculateVAT(item.total, item.vatRate),
    0
  );
  const total = subtotal + vatAmount;

  return { subtotal, vatAmount, total };
}

/**
 * Generate invoice
 */
export async function generateInvoice(
  request: InvoiceGenerateRequest
): Promise<Invoice> {
  // TODO: Get sequence number from database (Phase 7.5)
  const sequenceNumber = Math.floor(Math.random() * 1000) + 1;

  const invoiceNumber = generateInvoiceNumber(sequenceNumber);
  const date = new Date().toISOString();
  const dueDate = new Date(
    Date.now() + (request.dueInDays || 7) * 24 * 60 * 60 * 1000
  ).toISOString();

  const { subtotal, vatAmount, total } = calculateInvoiceTotals(request.items);

  const invoice: Invoice = {
    id: uuidv4(),
    number: invoiceNumber,
    date,
    dueDate,
    customer: request.customer,
    items: request.items,
    subtotal,
    vatAmount,
    total,
    currency: "RUB",
    status: "draft",
    notes: request.notes,
  };

  console.log("[Invoice] Generated:", invoice);

  // TODO: Save to database (Phase 7.5)

  return invoice;
}

/**
 * Mark invoice as sent
 */
export async function markInvoiceAsSent(invoiceId: string): Promise<Invoice> {
  // TODO: Update in database (Phase 7.5)
  console.log("[Invoice] Marked as sent:", invoiceId);

  // Mock response
  return {
    id: invoiceId,
    number: "AIM-2026-001",
    date: new Date().toISOString(),
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    customer: {
      name: "Стоматология Дента Плюс",
      email: "ivan@dentaplus.ru",
      inn: "7707083893",
    },
    items: [
      {
        description: "AI-маркетинг для медицинских клиник (месяц)",
        quantity: 1,
        unitPrice: 150000,
        vatRate: 20,
        total: 150000,
      },
    ],
    subtotal: 150000,
    vatAmount: 30000,
    total: 180000,
    currency: "RUB",
    status: "sent",
  };
}

/**
 * Mark invoice as paid
 */
export async function markInvoiceAsPaid(
  invoiceId: string,
  paymentMethod: string
): Promise<Invoice> {
  // TODO: Update in database (Phase 7.5)
  console.log("[Invoice] Marked as paid:", invoiceId, paymentMethod);

  // Mock response
  return {
    id: invoiceId,
    number: "AIM-2026-001",
    date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    dueDate: new Date().toISOString(),
    customer: {
      name: "Стоматология Дента Плюс",
      email: "ivan@dentaplus.ru",
      inn: "7707083893",
    },
    items: [
      {
        description: "AI-маркетинг для медицинских клиник (месяц)",
        quantity: 1,
        unitPrice: 150000,
        vatRate: 20,
        total: 150000,
      },
    ],
    subtotal: 150000,
    vatAmount: 30000,
    total: 180000,
    currency: "RUB",
    status: "paid",
    paymentMethod,
    paidAt: new Date().toISOString(),
  };
}

/**
 * Get invoice by ID
 */
export async function getInvoice(invoiceId: string): Promise<Invoice | null> {
  // TODO: Get from database (Phase 7.5)
  console.log("[Invoice] Getting invoice:", invoiceId);

  // Mock response
  return {
    id: invoiceId,
    number: "AIM-2026-001",
    date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    dueDate: new Date().toISOString(),
    customer: {
      name: "Стоматология Дента Плюс",
      email: "ivan@dentaplus.ru",
      inn: "7707083893",
    },
    items: [
      {
        description: "AI-маркетинг для медицинских клиник (месяц)",
        quantity: 1,
        unitPrice: 150000,
        vatRate: 20,
        total: 150000,
      },
    ],
    subtotal: 150000,
    vatAmount: 30000,
    total: 180000,
    currency: "RUB",
    status: "sent",
  };
}

/**
 * Get invoices for customer
 */
export async function getCustomerInvoices(
  customerEmail: string
): Promise<Invoice[]> {
  // TODO: Get from database (Phase 7.5)
  console.log("[Invoice] Getting customer invoices:", customerEmail);

  // Mock response
  return [
    {
      id: uuidv4(),
      number: "AIM-2026-001",
      date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() - 23 * 24 * 60 * 60 * 1000).toISOString(),
      customer: {
        name: "Стоматология Дента Плюс",
        email: customerEmail,
        inn: "7707083893",
      },
      items: [
        {
          description: "AI-маркетинг для медицинских клиник (месяц)",
          quantity: 1,
          unitPrice: 150000,
          vatRate: 20,
          total: 150000,
        },
      ],
      subtotal: 150000,
      vatAmount: 30000,
      total: 180000,
      currency: "RUB",
      status: "paid",
      paymentMethod: "bank_card",
      paidAt: new Date(Date.now() - 25 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: uuidv4(),
      number: "AIM-2026-002",
      date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date().toISOString(),
      customer: {
        name: "Стоматология Дента Плюс",
        email: customerEmail,
        inn: "7707083893",
      },
      items: [
        {
          description: "AI-маркетинг для медицинских клиник (месяц)",
          quantity: 1,
          unitPrice: 150000,
          vatRate: 20,
          total: 150000,
        },
      ],
      subtotal: 150000,
      vatAmount: 30000,
      total: 180000,
      currency: "RUB",
      status: "sent",
    },
  ];
}

/**
 * Format amount for display (150000 → "150 000 ₽")
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format date for display (ISO → "16 мая 2026")
 */
export function formatDate(isoDate: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(isoDate));
}
