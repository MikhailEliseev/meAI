'use client';

import { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, onStop, disabled, isStreaming, placeholder }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  const handleSend = () => {
    const message = value.trim();
    if (message && !disabled) {
      onSend(message);
      setValue('');
    }
  };

  return (
    <div className="flex gap-3 items-end p-4">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        placeholder={placeholder || 'Напишите адрес вашего сайта или задайте вопрос...'}
        disabled={disabled}
        rows={1}
        className="input-base flex-1 resize-none text-sm"
        aria-label="Сообщение"
      />

      {isStreaming ? (
        <button
          onClick={onStop}
          className="shrink-0 w-10 h-10 rounded-md bg-semantic-error text-white flex items-center justify-center hover:brightness-110 active:scale-95 transition-all duration-200"
          aria-label="Остановить"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <rect x="4" y="4" width="16" height="16" rx="2" />
          </svg>
        </button>
      ) : (
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="shrink-0 w-10 h-10 rounded-md bg-accent text-white flex items-center justify-center hover:brightness-110 active:scale-95 disabled:bg-surface-3 disabled:text-text-subtle disabled:cursor-not-allowed transition-all duration-200"
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
      )}
    </div>
  );
}
