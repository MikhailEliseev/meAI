'use client';

import { motion } from 'framer-motion';

interface ProgressIndicatorProps {
  progress: {
    step: string;
    stepIndex: number;
    totalSteps: number;
    liveMessage?: string;
  };
}

export function ProgressIndicator({ progress }: ProgressIndicatorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="self-start max-w-[85%]"
    >
      <div className="flex gap-3">
        <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-xs">AI</span>
        </div>

        <div className="bg-surface-2 rounded-lg px-4 py-3 border border-border-hairline flex-1">
          {progress.liveMessage ? (
            <motion.p
              key={progress.liveMessage}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-sm text-text-primary mb-2"
            >
              {progress.liveMessage}
            </motion.p>
          ) : (
            <p className="text-sm text-text-muted mb-2">{progress.step}</p>
          )}

          <div className="w-full bg-surface-3 rounded-full h-2">
            <motion.div
              className="h-2 rounded-full bg-accent"
              initial={{ width: 0 }}
              animate={{
                width: `${Math.round(
                  ((progress.stepIndex + 1) / Math.max(progress.totalSteps, 1)) * 100
                )}%`,
              }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
