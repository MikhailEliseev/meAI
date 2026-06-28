import React, { useState } from 'react';

export function FallbackForm({ sessionId, reportUrl, onClose }) {
  const [contact, setContact] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!contact.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/wp-json/aim/v1/fallback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contact: contact.trim(),
          session_id: sessionId,
          report_url: reportUrl || '',
        }),
      });

      if (!res.ok) throw new Error('Network error');

      const data = await res.json();
      if (!data.ok) throw new Error(data.message || 'Unknown error');

      setSuccess(true);
      setTimeout(onClose, 2000);
    } catch (err) {
      setError(err.message || 'Ошибка отправки');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4" onClick={onClose}>
      <div className="bg-surface-2 border border-border-hairline rounded-lg p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
        {success ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-ink mb-2">Отлично!</h3>
            <p className="text-sm text-text-muted">Отчёт будет отправлен после завершения анализа</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <h3 className="text-lg font-bold text-ink mb-4">Получить отчёт на почту или в Telegram</h3>
            <input
              type="text"
              value={contact}
              onChange={e => setContact(e.target.value)}
              placeholder="email@example.com или @telegram"
              className="w-full bg-bg border border-border-hairline rounded-lg px-4 py-3 text-sm text-ink placeholder:text-text-subtle focus:outline-none focus:border-accent transition-colors mb-4"
              disabled={loading}
              autoFocus
            />
            {error && (
              <p className="text-sm text-red-500 mb-4">{error}</p>
            )}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-surface-3 text-ink px-4 py-3 rounded-lg text-sm font-medium hover:bg-hover transition-all"
                disabled={loading}
              >
                Отмена
              </button>
              <button
                type="submit"
                className="flex-1 bg-accent text-white px-4 py-3 rounded-lg text-sm font-medium hover:brightness-110 transition-all disabled:opacity-50"
                disabled={loading || !contact.trim()}
              >
                {loading ? 'Отправка...' : 'Отправить'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
