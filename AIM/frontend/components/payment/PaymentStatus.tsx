/**
 * Payment Status Component
 *
 * Displays payment results with success/failure messages,
 * transaction details, and navigation options.
 *
 * Part of: Phase 11 Sprint 3 - Task 3.2
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { paymentAPI, PaymentStatusResponse } from "@/lib/api/payment";

interface PaymentStatusProps {
  paymentId: string;
}

export default function PaymentStatus({ paymentId }: PaymentStatusProps) {
  const router = useRouter();
  const [status, setStatus] = useState<PaymentStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await paymentAPI.getPaymentStatus(paymentId);
        setStatus(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load payment status");
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, [paymentId]);

  const handleDownloadReceipt = () => {
    // TODO: Implement receipt download
    window.open(`/api/payments/${paymentId}/receipt`, "_blank");
  };

  const handleReturnToDashboard = () => {
    router.push("/dashboard");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto mt-8 p-6 bg-surface-3 border border-semantic-error/30 rounded-md">
        <div className="flex items-center mb-4">
          <svg
            className="w-6 h-6 text-semantic-error mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h2 className="text-xl font-semibold text-semantic-error">Ошибка</h2>
        </div>
        <p className="text-semantic-error/80 mb-4">{error}</p>
        <button
          onClick={handleReturnToDashboard}
          className="w-full bg-semantic-error text-white py-2 px-4 rounded-md hover:brightness-110 transition-colors"
        >
          Вернуться в панель управления
        </button>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  const isSuccess = status.status === "completed";
  const isFailed = status.status === "failed";
  const isRefunded = status.status === "refunded";

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-surface-2 border border-border-hairline rounded-lg">
      {/* Status Icon and Title */}
      <div className="flex items-center justify-center mb-6">
        {isSuccess && (
          <div className="flex flex-col items-center">
            <svg
              className="w-16 h-16 text-semantic-success mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2 className="text-2xl font-bold text-semantic-success">Платёж успешен</h2>
          </div>
        )}

        {isFailed && (
          <div className="flex flex-col items-center">
            <svg
              className="w-16 h-16 text-semantic-error mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2 className="text-2xl font-bold text-semantic-error">Платёж не прошёл</h2>
          </div>
        )}

        {isRefunded && (
          <div className="flex flex-col items-center">
            <svg
              className="w-16 h-16 text-amber-400 mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
              />
            </svg>
            <h2 className="text-2xl font-bold text-amber-400">Платёж возвращён</h2>
          </div>
        )}
      </div>

      {/* Transaction Details */}
      <div className="space-y-3 mb-6">
        <div className="flex justify-between py-2 border-b border-border-hairline">
          <span className="text-text-muted">ID транзакции:</span>
          <span className="font-mono text-sm">{status.payment_id}</span>
        </div>

        <div className="flex justify-between py-2 border-b border-border-hairline">
          <span className="text-text-muted">Сумма:</span>
          <span className="font-semibold">
            {status.amount.toLocaleString("ru-RU")} {status.currency}
          </span>
        </div>

        <div className="flex justify-between py-2 border-b border-border-hairline">
          <span className="text-text-muted">Способ оплаты:</span>
          <span className="capitalize">{status.payment_method}</span>
        </div>

        {status.card_last4 && (
          <div className="flex justify-between py-2 border-b border-border-hairline">
            <span className="text-text-muted">Карта:</span>
            <span>
              {status.card_brand?.toUpperCase()} •••• {status.card_last4}
            </span>
          </div>
        )}

        {status.external_transaction_id && (
          <div className="flex justify-between py-2 border-b border-border-hairline">
            <span className="text-text-muted">Внешний ID:</span>
            <span className="font-mono text-sm">{status.external_transaction_id}</span>
          </div>
        )}

        <div className="flex justify-between py-2 border-b border-border-hairline">
          <span className="text-text-muted">Дата:</span>
          <span>{new Date(status.created_at).toLocaleString("ru-RU")}</span>
        </div>

        {status.completed_at && (
          <div className="flex justify-between py-2 border-b border-border-hairline">
            <span className="text-text-muted">Завершён:</span>
            <span>{new Date(status.completed_at).toLocaleString("ru-RU")}</span>
          </div>
        )}
      </div>

      {/* Error Message */}
      {isFailed && status.error_message && (
        <div className="mb-6 p-4 bg-surface-3 border border-semantic-error/30 rounded-md">
          <p className="text-sm text-semantic-error/80">
            <span className="font-semibold">Причина:</span> {status.error_message}
          </p>
          {status.error_code && (
            <p className="text-xs text-semantic-error mt-1">Код ошибки: {status.error_code}</p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-3">
        {isSuccess && (
          <button
            onClick={handleDownloadReceipt}
            className="w-full bg-accent text-white py-2 px-4 rounded-md hover:brightness-110 transition-colors flex items-center justify-center"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Скачать чек
          </button>
        )}

        <button
          onClick={handleReturnToDashboard}
          className="w-full bg-surface-3 text-text-muted py-2 px-4 rounded-md hover:bg-surface-2 transition-colors"
        >
          Вернуться в панель управления
        </button>
      </div>
    </div>
  );
}
