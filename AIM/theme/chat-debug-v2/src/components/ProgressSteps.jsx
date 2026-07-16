import React from 'react';

export function ProgressSteps({ progress }) {
  if (!progress) return null;
  const pct = Math.round(((progress.stepIndex + 1) / Math.max(progress.totalSteps, 1)) * 100);

  return (
    <div className="self-start max-w-[85%]">
      <div className="flex gap-3">
        <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-xs">AI</span>
        </div>
        <div className="bg-surface-2 rounded-lg px-4 py-3 border border-border-hairline flex-1">
          {progress.liveMessage ? (
            <p className="text-sm text-ink mb-2">{progress.liveMessage}</p>
          ) : (
            <p className="text-sm text-text-muted mb-2">{progress.step}</p>
          )}
          <div className="w-full bg-surface-3 rounded-full h-2">
            <div className="h-2 rounded-full bg-accent transition-all duration-500" style={{width: pct + '%'}} />
          </div>
        </div>
      </div>
    </div>
  );
}
