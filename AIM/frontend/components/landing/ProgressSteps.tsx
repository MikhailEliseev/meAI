"use client";

import React from "react";
import { motion } from "framer-motion";
import type { StreamProgress } from "@/hooks/useStreamChat";

interface ProgressStepsProps {
  progress: StreamProgress;
}

export function ProgressSteps({ progress }: ProgressStepsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="self-start max-w-[85%]"
    >
      <div className="flex gap-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-xs">AI</span>
        </div>
        <div className="bg-white rounded-2xl px-4 py-3 border border-gray-100 shadow-sm flex-1">
          <p className="text-sm text-gray-700 mb-2">{progress.step}</p>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="h-2 rounded-full bg-gradient-to-r from-primary-500 to-primary-700"
              initial={{ width: 0 }}
              animate={{
                width: `${Math.round(((progress.stepIndex + 1) / Math.max(progress.totalSteps, 1)) * 100)}%`,
              }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
