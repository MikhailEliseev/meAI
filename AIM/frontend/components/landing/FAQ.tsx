"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import faqData from "@/data/faq.json";

interface FAQItem {
  id: string;
  category: string;
  question: string;
  answer: string;
  tags: string[];
  views: number;
}

interface FAQProps {
  className?: string;
  limit?: number;
}

export function FAQ({ className, limit }: FAQProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  // Filter FAQs based on search and category
  const filteredFAQs = useMemo(() => {
    let filtered = faqData as FAQItem[];

    // Category filter
    if (selectedCategory !== "all") {
      filtered = filtered.filter((faq) => faq.category === selectedCategory);
    }

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (faq) =>
          faq.question.toLowerCase().includes(query) ||
          faq.answer.toLowerCase().includes(query) ||
          faq.tags.some((tag) => tag.toLowerCase().includes(query))
      );
    }

    // Apply limit if specified
    if (limit) {
      filtered = filtered.slice(0, limit);
    }

    return filtered;
  }, [searchQuery, selectedCategory, limit]);

  // Get unique categories
  const categories = useMemo(() => {
    const cats = Array.from(new Set(faqData.map((faq) => faq.category)));
    return [
      { id: "all", label: "Все вопросы" },
      { id: "security", label: "Безопасность" },
      { id: "results", label: "Результаты" },
      { id: "pricing", label: "Цены" },
      { id: "technology", label: "Технологии" },
      { id: "process", label: "Процесс" },
      { id: "expertise", label: "Экспертиза" },
      { id: "seo", label: "SEO" },
      { id: "onboarding", label: "Начало работы" },
    ];
  }, []);

  const toggleFAQ = (id: string) => {
    setOpenId(openId === id ? null : id);
  };

  // Schema.org FAQPage markup
  const schemaMarkup = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: filteredFAQs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.answer,
      },
    })),
  };

  return (
    <section
      className={cn("py-20 px-4 bg-white", className)}
      aria-labelledby="faq-heading"
    >
      <div className="max-w-4xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2
            id="faq-heading"
            className="font-heading text-3xl md:text-4xl font-bold text-gray-900 mb-4"
          >
            Часто задаваемые вопросы
          </h2>
          <p className="text-lg text-gray-600">
            Ответы на популярные вопросы о нашей работе
          </p>
        </motion.div>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <div className="relative">
            <input
              type="text"
              placeholder="Поиск по вопросам..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-6 py-4 pr-12 rounded-xl border-2 border-gray-200 focus:border-primary-500 focus:outline-none transition-colors text-gray-900 placeholder-gray-400"
              aria-label="Поиск по вопросам"
            />
            <span
              className="absolute right-4 top-1/2 transform -translate-y-1/2 text-2xl"
              aria-hidden="true"
            >
              🔍
            </span>
          </div>
        </motion.div>

        {/* Category Filter */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="mb-8 flex flex-wrap gap-2 justify-center"
        >
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium transition-all",
                selectedCategory === cat.id
                  ? "bg-primary-600 text-white shadow-md"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              )}
              aria-pressed={selectedCategory === cat.id}
            >
              {cat.label}
            </button>
          ))}
        </motion.div>

        {/* FAQ List */}
        <div className="space-y-4">
          {filteredFAQs.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12 text-gray-500"
            >
              <p className="text-lg">
                Вопросы не найдены. Попробуйте изменить запрос.
              </p>
            </motion.div>
          ) : (
            filteredFAQs.map((faq, index) => (
              <motion.div
                key={faq.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                className={cn(
                  "border-2 rounded-xl overflow-hidden transition-all",
                  openId === faq.id
                    ? "border-primary-500 shadow-lg"
                    : "border-gray-200 hover:border-gray-300"
                )}
              >
                {/* Question Button */}
                <button
                  onClick={() => toggleFAQ(faq.id)}
                  className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                  aria-expanded={openId === faq.id}
                  aria-controls={`faq-answer-${faq.id}`}
                >
                  <span className="font-semibold text-gray-900 pr-4">
                    {faq.question}
                  </span>
                  <motion.span
                    animate={{ rotate: openId === faq.id ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                    className="text-2xl text-primary-600 flex-shrink-0"
                    aria-hidden="true"
                  >
                    ▼
                  </motion.span>
                </button>

                {/* Answer */}
                <AnimatePresence>
                  {openId === faq.id && (
                    <motion.div
                      id={`faq-answer-${faq.id}`}
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-5 pt-2 border-t-2 border-gray-100">
                        <p className="text-gray-700 leading-relaxed mb-4">
                          {faq.answer}
                        </p>
                        {/* Tags */}
                        <div className="flex flex-wrap gap-2">
                          {faq.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))
          )}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mt-12"
        >
          <p className="text-gray-600 mb-4">
            Не нашли ответ на свой вопрос?
          </p>
          <button
            onClick={() => {
              const contactForm = document.getElementById("contact-form");
              if (contactForm) {
                contactForm.scrollIntoView({ behavior: "smooth" });
              }
            }}
            className="btn-primary"
            aria-label="Задать вопрос"
          >
            Задать вопрос
          </button>
        </motion.div>
      </div>

      {/* Schema.org Markup */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaMarkup) }}
      />
    </section>
  );
}
