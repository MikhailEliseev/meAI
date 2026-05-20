"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import caseStudiesData from "@/data/case-studies.json";

interface AwardProps {
  award: typeof caseStudiesData.awards[0];
  index: number;
}

function AwardCard({ award, index }: AwardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="bg-surface-2 rounded-lg p-6 border border-border-hairline hover:border-border-strong transition-all duration-300 hover:-translate-y-1"
    >
      {/* Icon */}
      <div className="text-5xl mb-4 text-center" aria-hidden="true">
        {award.icon}
      </div>

      {/* Title */}
      <h3 className="font-semibold text-ink text-center mb-2">
        {award.title}
      </h3>

      {/* Organization & Year */}
      <div className="text-sm text-text-muted text-center mb-3">
        {award.organization} • {award.year}
      </div>

      {/* Description */}
      <p className="text-xs text-text-subtle text-center leading-relaxed">
        {award.description}
      </p>
    </motion.div>
  );
}

interface AwardsProps {
  className?: string;
}

export function Awards({ className }: AwardsProps) {
  const awards = caseStudiesData.awards;

  return (
    <section
      className={cn("py-20 px-4 bg-canvas", className)}
      aria-labelledby="awards-heading"
    >

      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2
            id="awards-heading"
            className="text-3xl md:text-4xl font-bold text-ink mb-4"
          >
            Награды и сертификации
          </h2>
          <p className="text-lg text-text-muted max-w-2xl mx-auto">
            Наша экспертиза подтверждена ведущими организациями индустрии
          </p>
        </motion.div>

        {/* Awards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {awards.map((award, index) => (
            <AwardCard key={award.id} award={award} index={index} />
          ))}
        </div>

        {/* Trust Statement */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-16 text-center"
        >
          <div className="inline-flex items-center gap-3 px-6 py-4 bg-surface-3 rounded-full">
            <span className="text-2xl">🔒</span>
            <span className="text-sm font-semibold text-ink">
              Полное соответствие ФЗ-152 о защите персональных данных
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
