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
      className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-shadow duration-300"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 p-6 text-white">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="text-2xl font-bold mb-1">{caseStudy.title}</h3>
            <p className="text-primary-100 text-sm">
              {caseStudy.location} • {caseStudy.specialty}
            </p>
          </div>
          <div className="bg-white/20 px-3 py-1 rounded-full text-sm font-semibold">
            {caseStudy.results.timeframe}
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 p-6 bg-gray-50">
        {caseStudy.metrics.map((metric, idx) => (
          <div key={idx} className="text-center">
            <div className="text-3xl mb-1">{metric.icon}</div>
            <div className="text-2xl font-bold text-primary-600 mb-1">
              {metric.value}
            </div>
            <div className="text-xs text-gray-600">{metric.label}</div>
          </div>
        ))}
      </div>

      {/* Challenge & Solution */}
      <div className="p-6 space-y-4">
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Задача:</h4>
          <p className="text-gray-600 text-sm">{caseStudy.challenge}</p>
        </div>
        <div>
          <h4 className="font-semibold text-gray-900 mb-2">Решение:</h4>
          <p className="text-gray-600 text-sm">{caseStudy.solution}</p>
        </div>
      </div>

      {/* Tags */}
      <div className="px-6 pb-6">
        <div className="flex flex-wrap gap-2">
          {caseStudy.tags.map((tag, idx) => (
            <span
              key={idx}
              className="px-3 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* ROI Badge */}
      <div className="px-6 pb-6">
        <div className="bg-medical-green/10 border-2 border-medical-green rounded-lg p-4 text-center">
          <div className="text-sm text-gray-600 mb-1">ROI</div>
          <div className="text-3xl font-bold text-medical-green">
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
      className={cn("py-20 px-4 bg-gray-50", className)}
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
            className="font-heading text-3xl md:text-4xl font-bold text-gray-900 mb-4"
          >
            Наши кейсы
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
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
