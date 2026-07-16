import React from 'react';

const PHASES = [
  { id: 0,  name: 'Рынок',          stages: ['PERPLEXITY', 'perplexity', 'perplexity_search'] },
  { id: 1,  name: 'Конкуренты',     stages: ['COMPETITORS', 'competitors', 'find_competitors', 'run_ci_analysis', 'ci_analysis'] },
  { id: 2,  name: 'Тех. аудит',     stages: ['TECH AUDIT', 'tech_audit', 'run_pagespeed', 'run_tech_seo_audit', 'seo', 'run_lighthouse'] },
  { id: 3,  name: 'Отзывы',         stages: ['SOCIAL VERIFIER', 'social_verifier', 'run_review_platforms', 'reviews'] },
  { id: 4,  name: 'Контент',        stages: ['CONTENT ANALYSIS', 'content_analysis', 'run_content_analysis'] },
  { id: 5,  name: 'Врачи',          stages: ['KEY PERSONS', 'key_persons', 'find_doctor_handles', 'run_instagram_content', 'doctors', 'instagram'] },
  { id: 6,  name: 'СМИ',            stages: ['SMI MENTIONS', 'smi_mentions', 'run_smi_mentions', 'run_media_urls', 'media', 'smi'] },
  { id: 7,  name: 'Форумы',         stages: ['FORUM PAINS', 'forum_pains', 'run_forum_pains'] },
  { id: 8,  name: 'Финансы',        stages: ['FINANCE', 'finance', 'find_company_financials', 'financials'] },
  { id: 9,  name: 'Контент-план',   stages: ['CONTENT PLAN', 'content_plan', 'run_content_gaps'] },
  { id: 10, name: 'Сборка',         stages: ['HTML BUILD', 'html_build', 'generate_html_report', 'html_report'] },
  { id: 11, name: 'Проверка',       stages: ['QC CRITIQUE', 'qc_critique'] },
  { id: 12, name: 'Публикация',     stages: ['PRESENTATION', 'presentation', 'publish_scout_report', 'report-ready'] },
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
