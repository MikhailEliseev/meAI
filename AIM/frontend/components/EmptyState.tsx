'use client';

import { motion } from 'framer-motion';

const EXAMPLE_PROMPTS = [
  'Стоматология-Смайл.рф',
  'Косметология на Ленина, 15',
  'Многопрофильная клиника в Казани',
];

interface EmptyStateProps {
  onSend: (message: string) => void;
}

export function EmptyState({ onSend }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="flex flex-col items-center justify-center flex-1 px-4 py-16"
    >
      <div className="text-center max-w-lg mb-10">
        <h1 className="text-3xl md:text-4xl font-bold text-ink mb-4 leading-tight">
          AI-агент медицинского <span className="text-accent">маркетинга</span>
        </h1>
        <p className="text-base md:text-lg text-text-muted">
          Проанализирую вашу клинику, конкурентов и рынок. Покажу сколько пациентов вы теряете и
          как это исправить.
        </p>
      </div>

      <div className="w-full max-w-lg">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Введите адрес сайта вашей клиники..."
            className="input-base flex-1 text-sm"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                onSend(e.currentTarget.value.trim());
                e.currentTarget.value = '';
              }
            }}
          />
          <button
            onClick={() => {
              const input = document.querySelector<HTMLInputElement>(
                'input[placeholder="Введите адрес сайта вашей клиники..."]'
              );
              if (input?.value.trim()) {
                onSend(input.value.trim());
                input.value = '';
              }
            }}
            className="shrink-0 w-10 h-10 rounded-md bg-accent text-white flex items-center justify-center hover:brightness-110 active:scale-95 transition-all duration-200"
            aria-label="Отправить"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </button>
        </div>

        <div className="flex flex-wrap gap-2 mt-4 justify-center">
          {EXAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => onSend(prompt)}
              className="text-xs text-text-muted bg-surface-2 hover:bg-surface-3 rounded-full px-3 py-1.5 transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-center gap-4 mt-6 text-xs text-text-subtle">
          <span className="flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            Конфиденциально
          </span>
          <span className="flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            Бесплатно · 2 мин
          </span>
          <span className="flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            Без обязательств
          </span>
        </div>
      </div>
    </motion.div>
  );
}
