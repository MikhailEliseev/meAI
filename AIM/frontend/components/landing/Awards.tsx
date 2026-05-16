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
      className="bg-white rounded-xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
    >
      {/* Icon */}
      <div className="text-5xl mb-4 text-center" aria-hidden="true">
        {award.icon}
      </div>

      {/* Title */}
      <h3 className="font-semibold text-gray-900 text-center mb-2">
        {award.title}
      </h3>

      {/* Organization & Year */}
      <div className="text-sm text-gray-600 text-center mb-3">
        {award.organization} • {award.year}
      </div>

      {/* Description */}
      <p className="text-xs text-gray-500 text-center leading-relaxed">
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

  // Schema.org markup for organization
  const schemaMarkup = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "AIM Agency",
    "url": "https://iamaim.ru",
    "description": "AI-первое медицинское маркетинговое агентство",
    "award": awards.map((award) => award.title),
    "knowsAbout": [
      "Медицинский маркетинг",
      "AI-маркетинг",
      "SEO для клиник",
      "Яндекс.Директ",
      "Контент-маркетинг"
    ],
    "areaServed": {
      "@type": "Country",
      "name": "Россия"
    }
  };

  return (
    <section
      className={cn("py-20 px-4 bg-gradient-to-b from-gray-50 to-white", className)}
      aria-labelledby="awards-heading"
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
            id="awards-heading"
            className="font-heading text-3xl md:text-4xl font-bold text-gray-900 mb-4"
          >
            Награды и сертификации
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
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
          <div className="inline-flex items-center gap-3 px-6 py-4 bg-primary-50 rounded-full">
            <span className="text-2xl">🔒</span>
            <span className="text-sm font-semibold text-primary-900">
              Полное соответствие ФЗ-152 о защите персональных данных
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
