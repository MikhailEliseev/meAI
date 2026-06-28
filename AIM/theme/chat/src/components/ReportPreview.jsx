import React from 'react';

export function ReportPreview({ data, onRequestEmail }) {
  return (
    <div className="w-full max-w-3xl mx-auto px-4 mb-6" style={{animation: 'fadeIn 0.5s ease-out'}}>
      <div className="bg-surface-2 border border-border-hairline rounded-lg p-6">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-green-500/10 text-green-600 px-3 py-1 rounded-full text-xs font-medium mb-4">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Отчёт готов
        </div>

        {/* Title */}
        <h3 className="text-xl font-bold text-ink mb-4">{data.title}</h3>

        {/* Stats Grid */}
        {data.stats && data.stats.length > 0 && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            {data.stats.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-2xl font-bold text-accent">{stat.value}</div>
                <div className="text-xs text-text-muted mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* CTAs */}
        <div className="flex gap-3">
          <a
            href={data.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 bg-accent text-white text-center px-4 py-3 rounded-lg text-sm font-medium hover:brightness-110 transition-all"
          >
            Открыть полный отчёт →
          </a>
          <button
            onClick={onRequestEmail}
            className="flex-1 bg-surface-3 text-ink text-center px-4 py-3 rounded-lg text-sm font-medium border border-border-hairline hover:bg-hover transition-all"
          >
            Прислать на почту/TG
          </button>
        </div>
      </div>
    </div>
  );
}
