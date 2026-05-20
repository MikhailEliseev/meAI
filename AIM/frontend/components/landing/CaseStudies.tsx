"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import caseStudiesData from "@/data/case-studies.json";

interface CaseStudyProps {
  caseStudy: typeof caseStudiesData.caseStudies[0];
  index: number;
}

function CaseStudyCard({ caseStudy, index }: CaseStudyProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="bg-surface-2 rounded-lg border border-border-hairline overflow-hidden hover:border-border-strong transition-colors duration-300"
    >
      {/* Header */}
      <div className="bg-accent p-6 text-white">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="text-2xl font-bold mb-1">{caseStudy.title}</h3>
            <p className="text-white/70 text-sm">
              {caseStudy.location} • {caseStudy.specialty}
            </p>
          </div>
          <div className="bg-surface-2/50 px-3 py-1 rounded-full text-sm font-semibold">
            {caseStudy.results.timeframe}
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 p-6 bg-surface-1">
        {caseStudy.metrics.map((metric, idx) => (
          <div key={idx} className="text-center">
            <div className="text-3xl mb-1">{metric.icon}</div>
            <div className="text-2xl font-bold text-accent mb-1">
              {metric.value}
            </div>
            <div className="text-xs text-text-muted">{metric.label}</div>
          </div>
        ))}
      </div>

      {/* Challenge & Solution */}
      <div className="p-6 space-y-4">
        <div>
          <h4 className="font-semibold text-ink mb-2">Задача:</h4>
          <p className="text-text-muted text-sm">{caseStudy.challenge}</p>
        </div>
        <div>
          <h4 className="font-semibold text-ink mb-2">Решение:</h4>
          <p className="text-text-muted text-sm">{caseStudy.solution}</p>
        </div>
      </div>

      {/* Tags */}
      <div className="px-6 pb-6">
        <div className="flex flex-wrap gap-2">
          {caseStudy.tags.map((tag, idx) => (
            <span
              key={idx}
              className="px-3 py-1 bg-surface-3 text-accent text-xs font-medium rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* ROI Badge */}
      <div className="px-6 pb-6">
        <div className="bg-semantic-success/10 border border-semantic-success rounded-lg p-4 text-center">
          <div className="text-sm text-text-muted mb-1">ROI</div>
          <div className="text-3xl font-bold text-semantic-success">
            {caseStudy.results.roi}
          </div>
        </div>
      </div>
    </motion.article>
  );
}

interface CaseStudiesProps {
  className?: string;
  limit?: number;
}

export function CaseStudies({ className, limit }: CaseStudiesProps) {
  const studies = limit
    ? caseStudiesData.caseStudies.slice(0, limit)
    : caseStudiesData.caseStudies;

  // Schema.org markup for case studies
  const schemaMarkup = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "itemListElement": studies.map((study, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "item": {
        "@type": "Article",
        "headline": study.title,
        "description": study.challenge,
        "author": {
          "@type": "Organization",
          "name": "AIM Agency"
        }
      }
    }))
  };

  return (
    <section
      id="case-studies"
      className={cn("py-20 px-4 bg-surface-1", className)}
      aria-labelledby="case-studies-heading"
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaMarkup) }}
      />

      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2
            id="case-studies-heading"
            className="text-3xl md:text-4xl font-bold text-ink mb-4"
          >
            Наши кейсы
          </h2>
          <p className="text-lg text-text-muted max-w-2xl mx-auto">
            Реальные результаты наших клиентов. Каждый кейс — это история успеха
            медицинской клиники, которая доверилась AI-маркетингу.
          </p>
        </motion.div>

        {/* Case Studies Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {studies.map((study, index) => (
            <CaseStudyCard key={study.id} caseStudy={study} index={index} />
          ))}
        </div>

        {/* CTA */}
        {limit && caseStudiesData.caseStudies.length > limit && (
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mt-12"
          >
            <a
              href="/case-studies"
              className="btn-secondary inline-block"
              aria-label="Посмотреть все кейсы"
            >
              Посмотреть все кейсы ({caseStudiesData.caseStudies.length})
            </a>
          </motion.div>
        )}
      </div>
    </section>
  );
}
