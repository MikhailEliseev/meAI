import React from 'react';

// Средняя длительность каждой фазы в секундах (на основе логов Erasmile + arclinic)
const PHASE_DURATIONS = {
  0: 100,   // PERPLEXITY
  1: 130,   // COMPETITORS
  2: 90,    // TECH AUDIT
  3: 70,    // SOCIAL VERIFIER
  4: 110,   // CONTENT ANALYSIS
  5: 70,    // KEY PERSONS
  6: 65,    // SMI MENTIONS
  7: 45,    // FORUM PAINS
  8: 50,    // FINANCE
  9: 65,    // CONTENT PLAN
  10: 5,    // HTML BUILD
  11: 35,   // QC CRITIQUE
  12: 5,    // PRESENTATION
};

const PHASES = [
  { id: 0,  name: 'Рынок',          stages: ['PERPLEXITY', 'perplexity', 'perplexity_search'], desc: 'Исследую рынок' },
  { id: 1,  name: 'Конкуренты',     stages: ['COMPETITORS', 'competitors', 'find_competitors', 'run_ci_analysis', 'ci_analysis'], desc: 'Ищу конкурентов' },
  { id: 2,  name: 'Тех. аудит',     stages: ['TECH AUDIT', 'tech_audit', 'run_pagespeed', 'run_tech_seo_audit', 'seo', 'run_lighthouse'], desc: 'Анализирую тех. аудит' },
  { id: 3,  name: 'Отзывы',         stages: ['SOCIAL VERIFIER', 'social_verifier', 'run_review_platforms', 'reviews'], desc: 'Собираю отзывы' },
  { id: 4,  name: 'Контент',        stages: ['CONTENT ANALYSIS', 'content_analysis', 'run_content_analysis'], desc: 'Анализирую контент' },
  { id: 5,  name: 'Врачи',          stages: ['KEY PERSONS', 'key_persons', 'find_doctor_handles', 'run_instagram_content', 'doctors', 'instagram'], desc: 'Изучаю врачей' },
  { id: 6,  name: 'СМИ',            stages: ['SMI MENTIONS', 'smi_mentions', 'run_smi_mentions', 'run_media_urls', 'media', 'smi'], desc: 'Ищу упоминания в СМИ' },
  { id: 7,  name: 'Форумы',         stages: ['FORUM PAINS', 'forum_pains', 'run_forum_pains'], desc: 'Анализирую форумы' },
  { id: 8,  name: 'Финансы',        stages: ['FINANCE', 'finance', 'find_company_financials', 'financials'], desc: 'Собираю финансы' },
  { id: 9,  name: 'Контент-план',   stages: ['CONTENT PLAN', 'content_plan', 'run_content_gaps'], desc: 'Строю контент-план' },
  { id: 10, name: 'Сборка',         stages: ['HTML BUILD', 'html_build', 'generate_html_report', 'html_report'], desc: 'Собираю отчёт' },
  { id: 11, name: 'Проверка',       stages: ['QC CRITIQUE', 'qc_critique'], desc: 'Проверяю качество' },
  { id: 12, name: 'Публикация',     stages: ['PRESENTATION', 'presentation', 'publish_scout_report', 'report-ready'], desc: 'Публикую отчёт' },
];

/**
 * Рассчитать оставшееся время в секундах.
 * @param {number} currentPhaseId - ID текущей (working) фазы
 * @param {number} elapsedInCurrent - сколько секунд уже идёт текущая фаза
 * @returns {number} оставшиеся секунды
 */
export function calculateETA(currentPhaseId, elapsedInCurrent) {
  if (currentPhaseId === undefined || currentPhaseId === null) return 0;
  let remaining = 0;
  // Текущая фаза: вычитаем уже прошедшее время
  const currentDuration = PHASE_DURATIONS[currentPhaseId] || 60;
  remaining += Math.max(0, currentDuration - elapsedInCurrent);
  // Все будущие фазы
  for (let id = currentPhaseId + 1; id < PHASES.length; id++) {
    remaining += PHASE_DURATIONS[id] || 60;
  }
  return remaining;
}

function formatTime(seconds) {
  if (seconds <= 0) return 'почти готово';
  const mins = Math.ceil(seconds / 60);
  if (mins <= 1) return '~1 мин';
  return `~${mins} мин`;
}

export function PhaseTracker({ phases, etaSeconds, connectionWarning }) {
  const completedCount = phases.filter(p => p.status === 'done').length;
  const workingPhase = phases.find(p => p.status === 'working');
  const allDone = completedCount === phases.length;
  const progressPercent = Math.round((completedCount / phases.length) * 100);

  return (
    <div className="phase-tracker">
      {/* Header: progress + ETA */}
      <div className="phase-tracker-header">
        <span className="phase-tracker-count">{completedCount}/{phases.length}</span>
        {!allDone && workingPhase && (
          <span className="phase-tracker-eta">⏳ Осталось {formatTime(etaSeconds)}</span>
        )}
        {allDone && <span className="phase-tracker-done-badge">✓ Готово</span>}
      </div>

      {/* Progress bar */}
      <div className="phase-tracker-bar">
        <div
          className="phase-tracker-fill"
          style={{ width: `${progressPercent}%` }}
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
      {workingPhase && (
        <div className="phase-current">
          {workingPhase.counter || workingPhase.desc || workingPhase.name}…
        </div>
      )}

      {/* Connection warning */}
      {connectionWarning && (
        <div className="phase-connection-warning">{connectionWarning}</div>
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

export { PHASES, PHASE_DURATIONS };
