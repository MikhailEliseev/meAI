import React from 'react';

export function ReportPreview({ data, onRequestEmail }) {
  return (
    <div className="chat-report-card">
      <div className="chat-report-badge">
        <svg className="chat-report-badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        Отчёт готов
      </div>

      <h3 className="chat-report-title">{data.title}</h3>

      {data.stats && data.stats.length > 0 && (
        <div className="chat-report-stats">
          {data.stats.map((stat, i) => (
            <div key={i} className="chat-report-stat">
              <div className="chat-report-stat-value">{stat.value}</div>
              <div className="chat-report-stat-label">{stat.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="chat-report-actions">
        <a href={data.url} target="_blank" rel="noopener noreferrer" className="chat-btn chat-btn-primary chat-btn-full">
          Открыть полный отчёт →
        </a>
        <button onClick={onRequestEmail} className="chat-btn chat-btn-secondary chat-btn-full">
          Прислать на почту/TG
        </button>
      </div>
    </div>
  );
}
