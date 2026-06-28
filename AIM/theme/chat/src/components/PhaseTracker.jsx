import React from 'react';

const PHASES = [
  { id: 1, name: 'Анализ сайта', icon: '🔍', stages: ['run_prescan', 'prescan'] },
  { id: 2, name: 'Финансы', icon: '💰', stages: ['find_company_financials', 'financials', 'finance'] },
  { id: 3, name: 'Врачи и соцсети', icon: '👨‍⚕️', stages: ['find_doctor_handles', 'doctors', 'run_instagram_content', 'instagram'] },
  { id: 4, name: 'Конкуренты', icon: '🎯', stages: ['find_competitors', 'competitors', 'run_ci_analysis', 'ci_analysis'] },
  { id: 5, name: 'Отзывы', icon: '⭐', stages: ['run_review_platforms', 'reviews', 'run_forum_pains', 'forum_pains'] },
  { id: 6, name: 'СМИ', icon: '📰', stages: ['run_media_urls', 'media', 'smi'] },
  { id: 7, name: 'Технический аудит', icon: '⚙️', stages: ['run_tech_seo_audit', 'tech_seo', 'run_seo_audit', 'seo', 'run_lighthouse'] },
  { id: 8, name: 'Отчёт', icon: '📊', stages: ['generate_html_report', 'html_report', 'report'] },
];

export function PhaseTracker({ phases }) {
  const completedCount = phases.filter(p => p.status === 'done').length;
  const totalCount = phases.length;

  return (
    <div className="w-full max-w-3xl mx-auto px-4 mb-6">
      <div className="bg-surface-2 border border-border-hairline rounded-lg overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border-hairline flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${completedCount === totalCount ? 'bg-green-500' : 'bg-accent animate-pulse'}`} />
          <span className="font-semibold text-ink">Прогресс пресейла</span>
          <span className="text-text-muted text-sm ml-auto">{completedCount}/{totalCount}</span>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-border-hairline p-px">
          {phases.map(phase => (
            <PhaseCard key={phase.id} phase={phase} />
          ))}
        </div>
      </div>
    </div>
  );
}

function PhaseCard({ phase }) {
  const isPending = phase.status === 'pending';
  const isWorking = phase.status === 'working';
  const isDone = phase.status === 'done';

  return (
    <div className={`bg-surface-2 p-4 flex flex-col gap-2 transition-opacity ${isPending ? 'opacity-40' : 'opacity-100'}`}>
      <div className="flex items-center gap-2">
        <span className="text-2xl">{phase.icon}</span>
        {isWorking && <Spinner />}
        {isDone && <CheckIcon />}
      </div>
      <span className="text-xs font-medium text-ink">{phase.name}</span>
      {phase.counter && (
        <span className="text-xs text-text-muted">{phase.counter}</span>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg className="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export { PHASES };
