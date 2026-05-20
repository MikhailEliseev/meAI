"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ProcessStep {
  id: string;
  number: number;
  title: string;
  description: string;
  icon: string;
  duration: string;
  details: string[];
}

const steps: ProcessStep[] = [
  {
    id: "consultation",
    number: 1,
    title: "Бесплатная консультация",
    description: "Анализируем ваш бизнес и конкурентов с помощью AI",
    icon: "🎯",
    duration: "15 минут",
    details: [
      "AI-анализ вашего сайта и конкурентов",
      "Оценка текущей ситуации",
      "Выявление точек роста",
      "Расчёт потенциала рынка",
    ],
  },
  {
    id: "strategy",
    number: 2,
    title: "Персональная стратегия",
    description: "Создаём индивидуальный план привлечения пациентов",
    icon: "📊",
    duration: "3-5 дней",
    details: [
      "Подбор каналов привлечения",
      "Прогноз результатов и ROI",
      "Бюджет и сроки",
      "KPI и метрики успеха",
    ],
  },
  {
    id: "results",
    number: 3,
    title: "Реализация и результат",
    description: "Запускаем кампании и привлекаем пациентов",
    icon: "🚀",
    duration: "30 дней",
    details: [
      "Настройка рекламы и SEO",
      "AI-оптимизация 24/7",
      "Еженедельные отчёты",
      "Гарантия результата",
    ],
  },
];

interface ProcessStepCardProps {
  step: ProcessStep;
  index: number;
}

function ProcessStepCard({ step, index }: ProcessStepCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay: index * 0.2 }}
      className="relative"
    >
      {/* Step Card */}
      <div
        className={cn(
          "bg-surface-2 rounded-lg p-8 border border-border-hairline",
          "hover:border-accent transition-all duration-300",
          "hover:-translate-y-2"
        )}
      >
        {/* Step Number Badge */}
        <div className="absolute -top-6 left-8">
          <div className="w-12 h-12 bg-accent rounded-full flex items-center justify-center text-white font-bold text-xl">
            {step.number}
          </div>
        </div>

        {/* Icon */}
        <div className="text-6xl mb-4 text-center" aria-hidden="true">
          {step.icon}
        </div>

        {/* Title */}
        <h3 className="text-2xl font-bold text-ink mb-2 text-center">
          {step.title}
        </h3>

        {/* Duration */}
        <div className="text-center mb-4">
          <span className="inline-block px-4 py-1 bg-surface-3 text-accent rounded-full text-sm font-semibold">
            {step.duration}
          </span>
        </div>

        {/* Description */}
        <p className="text-text-muted text-center mb-6 leading-relaxed">
          {step.description}
        </p>

        {/* Details List */}
        <ul className="space-y-3">
          {step.details.map((detail, idx) => (
            <li key={idx} className="flex items-start gap-3">
              <span className="text-semantic-success text-xl flex-shrink-0" aria-hidden="true">
                ✓
              </span>
              <span className="text-text-muted text-sm">{detail}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Connector Arrow (desktop only) */}
      {index < steps.length - 1 && (
        <div className="hidden lg:block absolute top-1/2 -right-8 transform -translate-y-1/2 z-10">
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: index * 0.2 + 0.3 }}
            className="text-accent text-4xl"
            aria-hidden="true"
          >
            →
          </motion.div>
        </div>
      )}

      {/* Connector Arrow (mobile - vertical) */}
      {index < steps.length - 1 && (
        <div className="lg:hidden flex justify-center my-6">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: index * 0.2 + 0.3 }}
            className="text-accent text-4xl rotate-90"
            aria-hidden="true"
          >
            →
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}

interface ProcessStepsProps {
  className?: string;
}

export function ProcessSteps({ className }: ProcessStepsProps) {
  return (
    <section
      className={cn("py-20 px-4 bg-canvas", className)}
      aria-labelledby="process-heading"
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
            id="process-heading"
            className="text-3xl md:text-4xl font-bold text-ink mb-4"
          >
            Как мы работаем
          </h2>
          <p className="text-lg text-text-muted max-w-2xl mx-auto">
            Простой и прозрачный процесс от первой консультации до первых пациентов
          </p>
        </motion.div>

        {/* Process Steps Grid */}
        <div className="grid lg:grid-cols-3 gap-8 lg:gap-16 relative">
          {steps.map((step, index) => (
            <ProcessStepCard key={step.id} step={step} index={index} />
          ))}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mt-16"
        >
          <button
            onClick={() => {
              const contactForm = document.getElementById("contact-form");
              if (contactForm) {
                contactForm.scrollIntoView({ behavior: "smooth" });
              }
            }}
            className="btn-primary text-lg px-8 py-4"
            aria-label="Начать работу с AIM Agency"
          >
            Начать работу
          </button>
          <p className="text-sm text-text-subtle mt-4">
            Первая консультация бесплатно • Без обязательств
          </p>
        </motion.div>
      </div>
    </section>
  );
}
