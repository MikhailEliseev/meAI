"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "agent" | "user";
  content: string;
  timestamp: Date;
}

interface AuditProgress {
  stage: string;
  progress: number;
}

const WELCOME_MESSAGE = `Здравствуйте! Я AI-агент маркетингового агентства AIM.

Я могу прямо сейчас проанализировать вашу клинику и показать:
• Сколько пациентов вы теряете ежемесячно
• Сколько новых пациентов мы сможем привести
• За какое время и по какой стоимости

Просто отправьте мне адрес сайта вашей клиники 👇`;

const STAGES = [
  "Анализ сайта и SEO...",
  "Анализ контента и соцсетей...",
  "Оценка рекламного потенциала...",
  "Анализ конкурентов...",
  "Расчёт стоимости пациента...",
  "Формирование предложения...",
];

export function SalesChat({ className }: { className?: string }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "agent",
      content: WELCOME_MESSAGE,
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [auditStage, setAuditStage] = useState<AuditProgress | null>(null);
  const [leadId, setLeadId] = useState<string | null>(null);
  const [contactCollected, setContactCollected] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, auditStage, scrollToBottom]);

  const addMessage = (role: "agent" | "user", content: string) => {
    const msg: Message = {
      id: crypto.randomUUID(),
      role,
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, msg]);
    return msg;
  };

  const simulateAudit = async () => {
    setAuditStage({ stage: STAGES[0], progress: 0 });

    for (let i = 0; i < STAGES.length; i++) {
      await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));
      setAuditStage({ stage: STAGES[i], progress: Math.round(((i + 1) / STAGES.length) * 100) });
    }

    setAuditStage(null);
  };

  const handleSend = async (text: string) => {
    addMessage("user", text);
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          leadId,
          history: messages.slice(-10).map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      if (!response.ok) throw new Error("API error");

      const data = await response.json();

      if (data.leadId && !leadId) {
        setLeadId(data.leadId);
      }

      // Simulate audit progress then show result
      if (data.action === "run_audit") {
        await simulateAudit();
      }

      addMessage("agent", data.reply);

      if (data.contactCollected) {
        setContactCollected(true);
      }
    } catch (_err) {
      addMessage(
        "agent",
        "Извините, произошла ошибка. Пожалуйста, попробуйте ещё раз или напишите нам на почту."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section
      className={cn(
        "relative min-h-screen flex items-center justify-center",
        "bg-gradient-to-br from-primary-50 via-white to-primary-100",
        "px-4 py-20 md:py-32",
        className
      )}
      aria-labelledby="chat-heading"
    >
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-200 rounded-full opacity-20 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-medical-green/20 rounded-full opacity-20 blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto w-full">
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Left: Value proposition */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center lg:text-left pt-8"
          >
            <h1
              id="chat-heading"
              className="font-heading text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight"
            >
              Узнайте стоимость{" "}
              <span className="text-primary-600">нового пациента</span> за 2 минуты
            </h1>
            <p className="text-lg md:text-xl text-gray-600 mb-8">
              AI-агент проанализирует вашу клинику, конкурентов и рынок.
              Вы получите три главные цифры: пациенты, сроки, стоимость.
            </p>

            {/* Stats */}
            {contactCollected && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/80 backdrop-blur rounded-2xl p-6 border border-green-200"
              >
                <p className="text-green-700 font-medium mb-2">Спасибо! Мы зафиксировали ваши контакты.</p>
                <p className="text-sm text-gray-600">
                  Наш менеджер свяжется с вами в ближайшее время. Вы также можете продолжить общение с AI-агентом.
                </p>
              </motion.div>
            )}
          </motion.div>

          {/* Right: Chat window */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-gray-50 rounded-2xl shadow-xl border border-gray-100 overflow-hidden flex flex-col h-[600px]"
          >
            {/* Chat header */}
            <div className="bg-white px-5 py-4 border-b border-gray-100 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <div>
                <p className="font-medium text-gray-900 text-sm">AIM AI-агент</p>
                <p className="text-xs text-gray-500">
                  {isLoading ? "печатает..." : "онлайн"}
                </p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4">
              <AnimatePresence>
                {messages.map((msg) => (
                  <ChatBubble
                    key={msg.id}
                    role={msg.role}
                    content={msg.content}
                    timestamp={msg.timestamp}
                  />
                ))}
              </AnimatePresence>

              {/* Audit progress */}
              {auditStage && (
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
                      <p className="text-sm text-gray-700 mb-2">{auditStage.stage}</p>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <motion.div
                          className="h-2 rounded-full bg-gradient-to-r from-primary-500 to-primary-700"
                          initial={{ width: 0 }}
                          animate={{ width: `${auditStage.progress}%` }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Loading dots */}
              {isLoading && !auditStage && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="self-start flex gap-3"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                    <span className="text-white font-bold text-xs">AI</span>
                  </div>
                  <div className="bg-white rounded-2xl px-4 py-3 border border-gray-100">
                    <span className="inline-flex gap-1">
                      <span className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </span>
                  </div>
                </motion.div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <ChatInput
              onSend={handleSend}
              disabled={isLoading}
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
