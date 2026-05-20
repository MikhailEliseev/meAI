"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { Invoice } from "@/lib/payment/invoice-generator";
import { formatCurrency, formatDate } from "@/lib/payment/invoice-generator";

interface PaymentHistoryProps {
  customerEmail: string;
  className?: string;
}

export function PaymentHistory({
  customerEmail,
  className,
}: PaymentHistoryProps) {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "paid" | "pending" | "overdue">(
    "all"
  );

  useEffect(() => {
    fetchInvoices();
  }, [customerEmail]);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      // TODO: Replace with real API call (Phase 7.5)
      // Mock data for now
      await new Promise((resolve) => setTimeout(resolve, 500));

      const mockInvoices: Invoice[] = [
        {
          id: "1",
          number: "AIM-2026-001",
          date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
          dueDate: new Date(
            Date.now() - 53 * 24 * 60 * 60 * 1000
          ).toISOString(),
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
          paidAt: new Date(
            Date.now() - 55 * 24 * 60 * 60 * 1000
          ).toISOString(),
        },
        {
          id: "2",
          number: "AIM-2026-002",
          date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          dueDate: new Date(
            Date.now() - 23 * 24 * 60 * 60 * 1000
          ).toISOString(),
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
          paidAt: new Date(
            Date.now() - 25 * 24 * 60 * 60 * 1000
          ).toISOString(),
        },
        {
          id: "3",
          number: "AIM-2026-003",
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

      setInvoices(mockInvoices);
    } catch (error) {
      console.error("[Payment History] Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredInvoices = invoices.filter((invoice) => {
    if (filter === "all") return true;
    if (filter === "paid") return invoice.status === "paid";
    if (filter === "pending") return invoice.status === "sent";
    if (filter === "overdue") {
      return (
        invoice.status === "sent" && new Date(invoice.dueDate) < new Date()
      );
    }
    return true;
  });

  const getStatusBadge = (status: Invoice["status"]) => {
    const badges = {
      draft: { text: "Черновик", color: "bg-surface-3 text-text-muted" },
      sent: { text: "Отправлен", color: "bg-accent/15 text-accent" },
      paid: { text: "Оплачен", color: "bg-semantic-success/15 text-semantic-success" },
      overdue: { text: "Просрочен", color: "bg-semantic-error/15 text-semantic-error" },
      canceled: { text: "Отменён", color: "bg-surface-3 text-text-muted" },
    };

    const badge = badges[status] || badges.draft;

    return (
      <span
        className={cn(
          "px-3 py-1 rounded-full text-xs font-semibold",
          badge.color
        )}
      >
        {badge.text}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {[
          { value: "all", label: "Все" },
          { value: "paid", label: "Оплачены" },
          { value: "pending", label: "Ожидают оплаты" },
          { value: "overdue", label: "Просрочены" },
        ].map((item) => (
          <button
            key={item.value}
            onClick={() => setFilter(item.value as typeof filter)}
            className={cn(
              "px-4 py-2 rounded-md font-semibold transition-colors",
              filter === item.value
                ? "bg-accent text-white"
                : "bg-surface-3 text-text-muted hover:bg-surface-2"
            )}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Invoices List */}
      {filteredInvoices.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-text-muted">Счета не найдены</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredInvoices.map((invoice, index) => (
            <motion.div
              key={invoice.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-surface-2 rounded-lg p-6 border border-border-hairline hover:border-accent/30 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-ink">
                    {invoice.number}
                  </h3>
                  <p className="text-sm text-text-muted mt-1">
                    Выставлен: {formatDate(invoice.date)}
                  </p>
                  <p className="text-sm text-text-muted">
                    Оплатить до: {formatDate(invoice.dueDate)}
                  </p>
                </div>
                {getStatusBadge(invoice.status)}
              </div>

              {/* Items */}
              <div className="space-y-2 mb-4">
                {invoice.items.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex justify-between text-sm text-text-muted"
                  >
                    <span>
                      {item.description} × {item.quantity}
                    </span>
                    <span className="font-semibold">
                      {formatCurrency(item.total)}
                    </span>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="border-t border-border-hairline pt-4 space-y-2">
                <div className="flex justify-between text-sm text-text-muted">
                  <span>Сумма без НДС:</span>
                  <span>{formatCurrency(invoice.subtotal)}</span>
                </div>
                <div className="flex justify-between text-sm text-text-muted">
                  <span>НДС 20%:</span>
                  <span>{formatCurrency(invoice.vatAmount)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold text-ink">
                  <span>Итого:</span>
                  <span>{formatCurrency(invoice.total)}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 mt-4">
                <button className="flex-1 px-4 py-2 rounded-md bg-surface-3 text-text-muted font-semibold hover:bg-surface-2 transition-colors">
                  Скачать PDF
                </button>
                {invoice.status === "sent" && (
                  <button className="flex-1 px-4 py-2 rounded-md bg-accent text-white font-semibold hover:brightness-110 transition-colors">
                    Оплатить
                  </button>
                )}
              </div>

              {invoice.paidAt && (
                <p className="text-sm text-semantic-success mt-3">
                  ✓ Оплачен {formatDate(invoice.paidAt)}
                </p>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
