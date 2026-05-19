"use client";

import React, { useState, useRef, useEffect } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex gap-3 items-end p-4 bg-white border-t border-gray-100">
      <textarea
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || "Напишите адрес вашего сайта или задайте вопрос..."}
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none rounded-xl border border-gray-200 px-4 py-3 text-sm
                   focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                   disabled:bg-gray-50 disabled:text-gray-400
                   placeholder:text-gray-400"
        aria-label="Сообщение"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
        className="shrink-0 w-10 h-10 rounded-xl bg-primary-600 text-white
                   flex items-center justify-center
                   hover:bg-primary-700 active:scale-95
                   disabled:bg-gray-300 disabled:cursor-not-allowed
                   transition-all duration-200"
        aria-label="Отправить"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="19" x2="12" y2="5" />
          <polyline points="5 12 12 5 19 12" />
        </svg>
      </button>
    </div>
  );
}
