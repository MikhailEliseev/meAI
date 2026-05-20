"use client";

import React from "react";
import { motion } from "framer-motion";

interface EmptyChatProps {
  onSend: (text: string) => void;
}

const QUICK_ACTIONS = [
  "Стоматология-Смайл.рф",
  "Косметология на Ленина, 15",
  "Многопрофильная клиника в Казани",
];

export function EmptyChat({ onSend }: EmptyChatProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="flex flex-col items-center justify-center flex-1 px-4 py-16"
    >
      {/* Hero */}
      <div className="text-center max-w-lg mb-10">
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-gray-900 mb-4 leading-tight">
          AI-агент медицинского{" "}
          <span className="text-primary-600">маркетинга</span>
        </h1>
        <p className="text-base md:text-lg text-gray-600">
          Проанализирую вашу клинику, конкурентов и рынок.
          Покажу сколько пациентов вы теряете и как это исправить.
        </p>
      </div>

      {/* Centered input */}
      <div className="w-full max-w-lg">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Введите адрес сайта вашей клиники..."
            className="flex-1 rounded-xl border border-gray-200 px-4 py-3 text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                       placeholder:text-gray-400 shadow-sm"
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.currentTarget.value.trim()) {
                onSend(e.currentTarget.value.trim());
                e.currentTarget.value = "";
              }
            }}
          />
          <button
            onClick={() => {
              const input = document.querySelector<HTMLInputElement>(
                'input[placeholder="Введите адрес сайта вашей клиники..."]',
              );
              if (input?.value.trim()) {
                onSend(input.value.trim());
                input.value = "";
              }
            }}
            className="shrink-0 w-10 h-10 rounded-xl bg-primary-600 text-white
                       flex items-center justify-center
                       hover:bg-primary-700 active:scale-95
                       transition-all duration-200 shadow-sm"
            aria-label="Отправить"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </button>
        </div>

        {/* Quick actions */}
        <div className="flex flex-wrap gap-2 mt-4 justify-center">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action}
              onClick={() => onSend(action)}
              className="text-xs text-gray-500 bg-gray-100 hover:bg-gray-200 rounded-full px-3 py-1.5 transition-colors"
            >
              {action}
            </button>
          ))}
        </div>

        {/* Trust signals */}
        <div className="flex items-center justify-center gap-4 mt-6 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
            Конфиденциально
          </span>
          <span className="flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
            Бесплатно · 2 мин
          </span>
          <span className="flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
            Без обязательств
          </span>
        </div>
      </div>
    </motion.div>
  );
}
