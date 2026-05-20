"use client";

import React from "react";
import { motion } from "framer-motion";
import { TrustBadges } from "./TrustBadges";
import { cn } from "@/lib/utils";

interface HeroSectionProps {
  className?: string;
}

export function HeroSection({ className }: HeroSectionProps) {
  const handleCTAClick = () => {
    // Scroll to contact form
    const contactForm = document.getElementById("contact-form");
    if (contactForm) {
      contactForm.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <section
      className={cn(
        "relative min-h-screen flex items-center justify-center",
        "bg-canvas",
        "px-4 py-20 md:py-32",
        className
      )}
      aria-labelledby="hero-heading"
    >
      <div className="relative max-w-7xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left column: Text content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center lg:text-left"
          >
            {/* Headline */}
            <h1
              id="hero-heading"
              className="text-4xl md:text-5xl lg:text-6xl font-bold text-ink mb-6 leading-tight tracking-display-tight"
            >
              AI-маркетинг для{" "}
              <span className="text-accent">медицинских клиник</span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-text-muted mb-8 max-w-2xl mx-auto lg:mx-0">
              Привлекаем пациентов с помощью искусственного интеллекта.
              Гарантируем результат или возвращаем деньги.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start mb-12">
              <button
                onClick={handleCTAClick}
                className="btn-primary text-lg px-8 py-4"
                aria-label="Получить бесплатный аудит маркетинга"
              >
                Получить бесплатный аудит
              </button>
              <a
                href="#case-studies"
                className="btn-secondary text-lg px-8 py-4"
                aria-label="Посмотреть кейсы наших клиентов"
              >
                Посмотреть кейсы
              </a>
            </div>

            {/* Trust Badges */}
            <TrustBadges className="justify-center lg:justify-start" />
          </motion.div>

          {/* Right column: Visual/Stats */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="hidden lg:block"
          >
            <div className="relative">
              {/* Stats cards */}
              <div className="grid grid-cols-2 gap-6">
                <StatsCard
                  value="300%"
                  label="Средний рост трафика"
                  delay={0.3}
                />
                <StatsCard
                  value="50+"
                  label="Довольных клиентов"
                  delay={0.4}
                />
                <StatsCard
                  value="15K+"
                  label="Новых пациентов"
                  delay={0.5}
                />
                <StatsCard
                  value="24/7"
                  label="AI мониторинг"
                  delay={0.6}
                />
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

interface StatsCardProps {
  value: string;
  label: string;
  delay: number;
}

function StatsCard({ value, label, delay }: StatsCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="bg-surface-2 p-6 rounded-lg border border-border-hairline"
    >
      <div className="text-3xl font-bold text-accent mb-2">{value}</div>
      <div className="text-sm text-text-muted">{label}</div>
    </motion.div>
  );
}
