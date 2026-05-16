import { PaymentForm } from "@/components/payment/PaymentForm";
import { PaymentHistory } from "@/components/payment/PaymentHistory";

export const metadata = {
  title: "Биллинг | AIM Agency",
  description: "Управление платежами и счетами",
};

export default function BillingPage() {
  // TODO: Get customer email from session (Phase 7.5 auth)
  const customerEmail = "ivan@dentaplus.ru";

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
