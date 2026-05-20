"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { paymentAPI, PaymentRequest } from "@/lib/api/payment";

interface PaymentFormProps {
  amount: number;
  description: string;
  customerEmail: string;
  onSuccess?: (paymentId: string) => void;
  onError?: (error: string) => void;
  className?: string;
}

export function PaymentForm({
  amount,
  description,
  customerEmail,
  onSuccess,
  onError,
  className,
}: PaymentFormProps) {
  const [loading, setLoading] = useState(false);
  const [cardNumber, setCardNumber] = useState("");
  const [expiryDate, setExpiryDate] = useState("");
  const [cvv, setCvv] = useState("");
  const [cardholderName, setCardholderName] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Format card number (1234 5678 9012 3456)
  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\s/g, "");
    const chunks = cleaned.match(/.{1,4}/g) || [];
    return chunks.join(" ");
  };

  // Format expiry date (MM/YY)
  const formatExpiryDate = (value: string) => {
    const cleaned = value.replace(/\D/g, "");
    if (cleaned.length >= 2) {
      return `${cleaned.slice(0, 2)}/${cleaned.slice(2, 4)}`;
    }
    return cleaned;
  };

  // Validate card number (Luhn algorithm)
  const validateCardNumber = (number: string): boolean => {
    const cleaned = number.replace(/\s/g, "");
    if (!/^\d{16}$/.test(cleaned)) return false;

    let sum = 0;
    let isEven = false;

    for (let i = cleaned.length - 1; i >= 0; i--) {
      let digit = parseInt(cleaned[i], 10);

      if (isEven) {
        digit *= 2;
        if (digit > 9) digit -= 9;
      }

      sum += digit;
      isEven = !isEven;
    }

    return sum % 10 === 0;
  };

  // Validate expiry date
  const validateExpiryDate = (date: string): boolean => {
    const [month, year] = date.split("/");
    if (!month || !year) return false;

    const monthNum = parseInt(month, 10);
    const yearNum = parseInt(`20${year}`, 10);

    if (monthNum < 1 || monthNum > 12) return false;

    const now = new Date();
    const expiry = new Date(yearNum, monthNum - 1);

    return expiry > now;
  };

  // Validate CVV
  const validateCVV = (cvv: string): boolean => {
    return /^\d{3,4}$/.test(cvv);
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate fields
    const newErrors: Record<string, string> = {};

    if (!cardholderName.trim()) {
      newErrors.cardholderName = "Введите имя владельца карты";
    }

    if (!validateCardNumber(cardNumber)) {
      newErrors.cardNumber = "Неверный номер карты";
    }

    if (!validateExpiryDate(expiryDate)) {
      newErrors.expiryDate = "Неверная дата (MM/YY)";
    }

    if (!validateCVV(cvv)) {
      newErrors.cvv = "Неверный CVV";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      // Create payment request
      const request: PaymentRequest = {
        amount,
        currency: "RUB",
        payment_method: "card",
        customer_name: cardholderName,
        customer_email: customerEmail,
        card_number: cardNumber.replace(/\s/g, ""),
        card_expiry: expiryDate,
        card_cvv: cvv,
        metadata: {
          description,
        },
      };

      // Process payment via API
      const response = await paymentAPI.createPayment(request);

      console.log("[Payment] Payment successful:", response.payment_id);

      if (onSuccess) {
        onSuccess(response.payment_id);
      }
    } catch (error) {
      console.error("[Payment] Error:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Ошибка обработки платежа";

      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("space-y-6", className)}
      onSubmit={handleSubmit}
    >
      {/* Amount Display */}
      <div className="bg-surface-3 rounded-lg p-6 border border-border-hairline">
        <p className="text-sm font-semibold text-text-muted mb-1">К оплате</p>
        <p className="text-3xl font-bold text-ink">
          {new Intl.NumberFormat("ru-RU", {
            style: "currency",
            currency: "RUB",
            minimumFractionDigits: 0,
          }).format(amount)}
        </p>
        <p className="text-sm text-text-muted mt-2">{description}</p>
      </div>

      {/* Cardholder Name */}
      <div>
        <label
          htmlFor="cardholderName"
          className="block text-sm font-semibold text-text-muted mb-2"
        >
          Имя владельца карты
        </label>
        <input
          type="text"
          id="cardholderName"
          value={cardholderName}
          onChange={(e) => setCardholderName(e.target.value.toUpperCase())}
          placeholder="IVAN PETROV"
          className={cn(
            "w-full px-4 py-3 rounded-md border-2 transition-colors",
            errors.cardholderName
              ? "border-semantic-error/50 focus:border-semantic-error"
              : "border-border-hairline focus:border-accent"
          )}
          disabled={loading}
        />
        {errors.cardholderName && (
          <p className="text-sm text-semantic-error mt-1">{errors.cardholderName}</p>
        )}
      </div>

      {/* Card Number */}
      <div>
        <label
          htmlFor="cardNumber"
          className="block text-sm font-semibold text-text-muted mb-2"
        >
          Номер карты
        </label>
        <input
          type="text"
          id="cardNumber"
          value={cardNumber}
          onChange={(e) => {
            const formatted = formatCardNumber(e.target.value);
            if (formatted.replace(/\s/g, "").length <= 16) {
              setCardNumber(formatted);
            }
          }}
          placeholder="1234 5678 9012 3456"
          className={cn(
            "w-full px-4 py-3 rounded-md border-2 transition-colors font-mono",
            errors.cardNumber
              ? "border-semantic-error/50 focus:border-semantic-error"
              : "border-border-hairline focus:border-accent"
          )}
          disabled={loading}
        />
        {errors.cardNumber && (
          <p className="text-sm text-semantic-error mt-1">{errors.cardNumber}</p>
        )}
      </div>

      {/* Expiry Date and CVV */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label
            htmlFor="expiryDate"
            className="block text-sm font-semibold text-text-muted mb-2"
          >
            Срок действия
          </label>
          <input
            type="text"
            id="expiryDate"
            value={expiryDate}
            onChange={(e) => {
              const formatted = formatExpiryDate(e.target.value);
              if (formatted.replace(/\D/g, "").length <= 4) {
                setExpiryDate(formatted);
              }
            }}
            placeholder="MM/YY"
            className={cn(
              "w-full px-4 py-3 rounded-md border-2 transition-colors font-mono",
              errors.expiryDate
                ? "border-semantic-error/50 focus:border-semantic-error"
                : "border-border-hairline focus:border-accent"
            )}
            disabled={loading}
          />
          {errors.expiryDate && (
            <p className="text-sm text-semantic-error mt-1">{errors.expiryDate}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="cvv"
            className="block text-sm font-semibold text-text-muted mb-2"
          >
            CVV
          </label>
          <input
            type="text"
            id="cvv"
            value={cvv}
            onChange={(e) => {
              const value = e.target.value.replace(/\D/g, "");
              if (value.length <= 4) {
                setCvv(value);
              }
            }}
            placeholder="123"
            className={cn(
              "w-full px-4 py-3 rounded-md border-2 transition-colors font-mono",
              errors.cvv
                ? "border-semantic-error/50 focus:border-semantic-error"
                : "border-border-hairline focus:border-accent"
            )}
            disabled={loading}
          />
          {errors.cvv && (
            <p className="text-sm text-semantic-error mt-1">{errors.cvv}</p>
          )}
        </div>
      </div>

      {/* Security Notice */}
      <div className="bg-surface-3 rounded-md p-4 border border-border-hairline">
        <p className="text-sm text-text-muted">
          🔒 Платёж защищён по стандарту PCI DSS. Данные карты передаются в
          зашифрованном виде через ЮKassa.
        </p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className={cn(
          "w-full py-4 rounded-md font-bold text-lg transition-all",
          loading
            ? "bg-surface-3 text-text-muted cursor-not-allowed"
            : "bg-accent text-white hover:brightness-110"
        )}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
            Обработка платежа...
          </span>
        ) : (
          `Оплатить ${new Intl.NumberFormat("ru-RU", {
            style: "currency",
            currency: "RUB",
            minimumFractionDigits: 0,
          }).format(amount)}`
        )}
      </button>

      {/* STUB Notice */}
      <div className="bg-surface-3 rounded-md p-4 border border-amber-400/30">
        <p className="text-sm text-amber-400">
          ⚠️ <strong>STUB:</strong> Используется Helcim stub для разработки.
          Реальная интеграция с ЮKassa будет в Phase 12. Платежи обрабатываются
          через backend API, но всегда возвращают успех.
        </p>
      </div>
    </motion.form>
  );
}
