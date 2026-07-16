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
    <div className="chat-input-bar">
      <textarea
        ref={inputRef}
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Напишите адрес вашего сайта или задайте вопрос...'}
        disabled={disabled}
        rows={1}
        className="chat-input-field"
        aria-label="Сообщение"
      />
      {isStreaming ? (
        <button onClick={onStop} className="chat-btn chat-btn-danger" aria-label="Остановить">
          Стоп
        </button>
      ) : (
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="chat-btn chat-btn-primary"
          aria-label="Отправить"
        >
          Отправить
        </button>
      )}
    </div>
  );
}
