import React from 'react';

const PHASES = [
  { id: 1, name: 'Анализ сайта', stages: ['run_prescan', 'prescan'] },
  { id: 2, name: 'Финансы', stages: ['find_company_financials', 'financials', 'finance', 'perplexity'] },
  { id: 3, name: 'Врачи и соцсети', stages: ['find_doctor_handles', 'doctors', 'run_instagram_content', 'instagram'] },
  { id: 4, name: 'Конкуренты', stages: ['find_competitors', 'competitors', 'run_ci_analysis', 'ci_analysis'] },
  { id: 5, name: 'Отзывы', stages: ['run_review_platforms', 'reviews', 'run_forum_pains', 'forum_pains'] },
  { id: 6, name: 'СМИ', stages: ['run_media_urls', 'media', 'smi'] },
  { id: 7, name: 'Технический аудит', stages: ['run_tech_seo_audit', 'tech_seo', 'run_seo_audit', 'seo', 'run_lighthouse'] },
  { id: 8, name: 'Отчёт', stages: ['generate_html_report', 'html_report', 'report', 'report-ready'] },
];

export function PhaseTracker({ phases }) {
  const completedCount = phases.filter(p => p.status === 'done').length;
  const workingPhase = phases.find(p => p.status === 'working');

  return (
    <div className="phase-tracker">
      {/* Progress bar */}
      <div className="phase-tracker-bar">
        <div
          className="phase-tracker-fill"
          style={{ width: `${Math.round((completedCount / phases.length) * 100)}%` }}
        />
      </div>

      {/* Labels row */}
      <div className="phase-tracker-labels">
        {phases.map(phase => {
          const isDone = phase.status === 'done';
          const isWorking = phase.status === 'working';
          return (
            <span
              key={phase.id}
              className={`phase-label ${isDone ? 'done' : ''} ${isWorking ? 'working' : ''}`}
            >
              {isWorking && <span className="phase-spinner" />}
              {isDone && <CheckSmall />}
              {phase.name}
              {phase.counter && <span className="phase-counter">{phase.counter}</span>}
            </span>
          );
        })}
      </div>

      {/* Current action text */}
      {workingPhase && workingPhase.counter && (
        <div className="phase-current">{workingPhase.counter}</div>
      )}
    </div>
  );
}

function CheckSmall() {
  return (
    <svg className="phase-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export { PHASES };
