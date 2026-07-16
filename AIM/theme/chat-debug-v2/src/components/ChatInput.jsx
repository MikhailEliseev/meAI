import React, { useState, useRef, useEffect } from 'react';

export function ChatInput({ onSend, onStop, disabled, isStreaming, placeholder }) {
  const [value, setValue] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (!disabled && inputRef.current) inputRef.current.focus();
  }, [disabled]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex gap-3 items-end p-4">
      <textarea
        ref={inputRef}
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Напишите адрес вашего сайта или задайте вопрос...'}
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none text-sm bg-surface-2 border border-border-hairline rounded-lg px-4 py-3 text-ink placeholder:text-text-subtle focus:outline-none focus:border-accent transition-colors"
        aria-label="Сообщение"
      />
      {isStreaming ? (
        <button
          onClick={onStop}
          className="shrink-0 w-10 h-10 rounded-md bg-red-500 text-white flex items-center justify-center hover:brightness-110 active:scale-95 transition-all"
          aria-label="Остановить"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2" /></svg>
        </button>
      ) : (
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="shrink-0 w-10 h-10 rounded-md bg-accent text-white flex items-center justify-center hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          aria-label="Отправить"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="19" x2="12" y2="5" /><polyline points="5 12 12 5 19 12" /></svg>
        </button>
      )}
    </div>
  );
}
