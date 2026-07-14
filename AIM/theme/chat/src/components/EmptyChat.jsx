import React, { useState, useRef } from 'react';

const QUICK_ACTIONS = [
  'Стоматология-Смайл.рф',
  'Косметология на Ленина, 15',
  'Многопрофильная клиника в Казани',
];

export function EmptyChat({ onSend }) {
  const [value, setValue] = useState('');
  const inputRef = useRef(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="chat-empty-screen">
      <div className="chat-empty-title-block">
        <h1>AI-агент медицинского <span className="text-accent">маркетинга</span></h1>
        <p>Проанализирую вашу клинику, конкурентов и рынок. Покажу сколько пациентов вы теряете и как это исправить.</p>
      </div>
      <div className="chat-empty-input-block">
        <div className="chat-empty-input-row">
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Введите адрес сайта вашей клиники..."
            className="chat-empty-input"
          />
          <button onClick={handleSubmit} disabled={!value.trim()} className="chat-btn chat-btn-primary">
            Отправить
          </button>
        </div>
        <div className="chat-empty-chips">
          {QUICK_ACTIONS.map(action => (
            <button key={action} onClick={() => onSend(action)} className="chat-btn chat-btn-ghost">
              {action}
            </button>
          ))}
        </div>
        <div className="chat-empty-badges">
          <span className="chat-badge">🛡️ Конфиденциально</span>
          <span className="chat-badge">⏱️ Бесплатно · 15 мин</span>
          <span className="chat-badge">✓ Без обязательств</span>
        </div>
      </div>
    </div>
  );
}
