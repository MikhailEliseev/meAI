"use client";

import { useState, useEffect } from "react";
import { PaymentForm } from "@/components/payment/PaymentForm";
import { PaymentHistory } from "@/components/payment/PaymentHistory";

export const dynamic = "force-dynamic";

export default function BillingPage() {
  const [customerEmail, setCustomerEmail] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProfile() {
      try {
        const res = await fetch("/api/dashboard/progress");
        if (res.ok) {
          // TODO: Get actual email from auth session / profile API (Phase 7.5)
          setCustomerEmail("client@iamaim.ru");
        }
      } catch {
        // fallback
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-10 w-10 border-4 border-primary-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-heading text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Биллинг
          </h1>
          <p className="text-lg text-gray-600">
            Управление платежами и счетами
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Payment Form */}
          <div>
            <h2 className="font-heading text-2xl font-bold text-gray-900 mb-4">
              Оплата подписки
            </h2>
            <PaymentForm
              amount={180000} // 150K + 20% VAT
              description="AI-маркетинг для медицинских клиник (месяц)"
              customerEmail={customerEmail}
              onSuccess={(paymentId) => {
                console.log("Payment successful:", paymentId);
                // TODO: Redirect to success page
              }}
              onError={(error) => {
                console.error("Payment error:", error);
                // TODO: Show error notification
              }}
            />
          </div>

          {/* Payment History */}
          <div>
            <h2 className="font-heading text-2xl font-bold text-gray-900 mb-4">
              История платежей
            </h2>
            <PaymentHistory customerEmail={customerEmail} />
          </div>
        </div>
      </div>
    </div>
  );
}
