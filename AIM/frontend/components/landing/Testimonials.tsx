"use client";

import React from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import { cn } from "@/lib/utils";
import caseStudiesData from "@/data/case-studies.json";

interface TestimonialProps {
  testimonial: typeof caseStudiesData.caseStudies[0]["testimonial"];
  caseStudy: typeof caseStudiesData.caseStudies[0];
  index: number;
}

function TestimonialCard({ testimonial, caseStudy, index }: TestimonialProps) {
  return (
    <motion.article
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="bg-surface-2 rounded-lg p-8 border border-border-hairline hover:border-border-strong transition-colors duration-300"
    >
      {/* Quote Icon */}
      <div className="text-accent text-5xl mb-4" aria-hidden="true">
        "
      </div>

      {/* Testimonial Text */}
      <blockquote className="text-text-muted text-lg mb-6 leading-relaxed">
        {testimonial.text}
      </blockquote>

      {/* Author Info */}
      <div className="flex items-center gap-4 pt-6 border-t border-border-hairline">
        <div className="relative w-16 h-16 rounded-full overflow-hidden bg-surface-3 flex-shrink-0">
          {/* Placeholder for photo - in production, use real images */}
          <div className="w-full h-full flex items-center justify-center bg-accent text-white text-2xl font-bold">
            {testimonial.author.charAt(0)}
          </div>
        </div>
        <div>
          <div className="font-semibold text-ink">{testimonial.author}</div>
          <div className="text-sm text-text-muted">{testimonial.position}</div>
          <div className="text-xs text-accent mt-1">
            {caseStudy.title}
          </div>
        </div>
      </div>

      {/* Results Badge */}
      <div className="mt-6 flex items-center gap-2 text-sm">
        <span className="px-3 py-1 bg-semantic-success/10 text-semantic-success rounded-full font-semibold">
          ROI {caseStudy.results.roi}
        </span>
        <span className="px-3 py-1 bg-surface-3 text-accent rounded-full font-semibold">
          {caseStudy.results.trafficGrowth} трафика
        </span>
      </div>
    </motion.article>
  );
}

interface TestimonialsProps {
  className?: string;
  limit?: number;
}

export function Testimonials({ className, limit = 3 }: TestimonialsProps) {
  const testimonials = limit
    ? caseStudiesData.caseStudies.slice(0, limit)
    : caseStudiesData.caseStudies;

  // Schema.org markup for reviews
  const schemaMarkup = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "AIM Agency",
    "url": "https://iamaim.ru",
    "review": testimonials.map((study) => ({
      "@type": "Review",
      "reviewRating": {
        "@type": "Rating",
        "ratingValue": "5",
        "bestRating": "5"
      },
      "author": {
        "@type": "Person",
        "name": study.testimonial.author
      },
      "reviewBody": study.testimonial.text,
      "itemReviewed": {
        "@type": "Service",
        "name": "AI-маркетинг для медицинских клиник"
      }
    }))
  };

  return (
    <section
      className={cn("py-20 px-4 bg-canvas", className)}
      aria-labelledby="testimonials-heading"
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
            id="testimonials-heading"
            className="text-3xl md:text-4xl font-bold text-ink mb-4"
          >
            Что говорят наши клиенты
          </h2>
          <p className="text-lg text-text-muted max-w-2xl mx-auto">
            Отзывы руководителей медицинских клиник, которые уже получили результат
            от работы с AIM Agency.
          </p>
        </motion.div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((study, index) => (
            <TestimonialCard
              key={study.id}
              testimonial={study.testimonial}
              caseStudy={study}
              index={index}
            />
          ))}
        </div>

        {/* Stats Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 text-center"
        >
          <div>
            <div className="text-4xl font-bold text-accent mb-2">50+</div>
            <div className="text-text-muted">Довольных клиентов</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-accent mb-2">15K+</div>
            <div className="text-text-muted">Новых пациентов</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-accent mb-2">450%</div>
            <div className="text-text-muted">Средний ROI</div>
          </div>
          <div>
            <div className="text-4xl font-bold text-accent mb-2">98%</div>
            <div className="text-text-muted">Продлевают контракт</div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
