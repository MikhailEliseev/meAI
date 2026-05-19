"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { cn } from "@/lib/utils";

interface AnalyticsDashboardProps {
  className?: string;
}

type TabType = "leads" | "email" | "queue";

export function AnalyticsDashboard({ className }: AnalyticsDashboardProps) {
  const [activeTab, setActiveTab] = useState<TabType>("leads");
  const [leadData, setLeadData] = useState<any>(null);
  const [emailData, setEmailData] = useState<any>(null);
  const [queueData, setQueueData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch analytics data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [leadsRes, emailRes, queueRes] = await Promise.all([
          fetch("/api/analytics/leads"),
          fetch("/api/analytics/email"),
          fetch("/api/email/queue-stats"),
        ]);

        const [leads, email, queue] = await Promise.all([
          leadsRes.json(),
          emailRes.json(),
          queueRes.json(),
        ]);

        setLeadData(leads.data);
        setEmailData(email.data);
        setQueueData(queue.stats);
      } catch (error) {
        console.error("[Analytics] Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const COLORS = {
    hot: "#ef4444", // red-500
    warm: "#f59e0b", // amber-500
    cold: "#3b82f6", // blue-500
    primary: "#0ea5e9", // sky-500
    success: "#10b981", // emerald-500
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className={cn("py-20 px-4 bg-gray-50", className)}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="font-heading text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Аналитика
          </h1>
          <p className="text-lg text-gray-600">
            Отслеживайте эффективность лидов и email-кампаний
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-4 mb-8 border-b border-gray-200">
          <button
            onClick={() => setActiveTab("leads")}
            className={cn(
              "px-6 py-3 font-semibold transition-colors border-b-2",
              activeTab === "leads"
                ? "text-primary-600 border-primary-600"
                : "text-gray-600 border-transparent hover:text-gray-900"
            )}
          >
            Лиды
          </button>
          <button
            onClick={() => setActiveTab("email")}
            className={cn(
              "px-6 py-3 font-semibold transition-colors border-b-2",
              activeTab === "email"
                ? "text-primary-600 border-primary-600"
                : "text-gray-600 border-transparent hover:text-gray-900"
            )}
          >
            Email
          </button>
          <button
            onClick={() => setActiveTab("queue")}
            className={cn(
              "px-6 py-3 font-semibold transition-colors border-b-2",
              activeTab === "queue"
                ? "text-primary-600 border-primary-600"
                : "text-gray-600 border-transparent hover:text-gray-900"
            )}
          >
            Очередь
          </button>
        </div>

        {/* Lead Analytics */}
        {activeTab === "leads" && leadData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <SummaryCard
                title="Всего лидов"
                value={leadData.summary.totalLeads}
                color="primary"
              />
              <SummaryCard
                title="Горячие лиды"
                value={leadData.summary.hotLeads}
                color="hot"
              />
              <SummaryCard
                title="Средний балл"
                value={leadData.summary.averageScore.toFixed(1)}
                color="primary"
              />
              <SummaryCard
                title="Конверсия"
                value={`${(leadData.summary.conversionRate * 100).toFixed(1)}%`}
                color="success"
              />
            </div>

            {/* Tier Breakdown */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-heading text-xl font-bold text-gray-900 mb-4">
                Распределение по уровням
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={leadData.tierBreakdown}
                    dataKey="count"
                    nameKey="tier"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={(entry) => `${entry.name}: ${((entry.percent ?? 0) * 100).toFixed(1)}%`}
                  >
                    {leadData.tierBreakdown.map((entry: any, index: number) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[entry.tier as keyof typeof COLORS]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Daily Leads */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-heading text-xl font-bold text-gray-900 mb-4">
                Лиды по дням
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={leadData.dailyLeads}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="hot" fill={COLORS.hot} name="Горячие" />
                  <Bar dataKey="warm" fill={COLORS.warm} name="Тёплые" />
                  <Bar dataKey="cold" fill={COLORS.cold} name="Холодные" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top Specialties */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-heading text-xl font-bold text-gray-900 mb-4">
                Топ специализаций
              </h3>
              <div className="space-y-4">
                {leadData.topSpecialties.map((spec: any, index: number) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-gray-900">
                          {spec.specialty}
                        </span>
                        <span className="text-sm text-gray-600">
                          {spec.count} лидов • {spec.avgScore.toFixed(1)} балл
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full"
                          style={{
                            width: `${(spec.count / leadData.summary.totalLeads) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Email Analytics */}
        {activeTab === "email" && emailData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <SummaryCard
                title="Отправлено"
                value={emailData.summary.totalSent}
                color="primary"
              />
              <SummaryCard
                title="Open Rate"
                value={`${(emailData.summary.openRate * 100).toFixed(1)}%`}
                color="success"
              />
              <SummaryCard
                title="Click Rate"
                value={`${(emailData.summary.clickRate * 100).toFixed(1)}%`}
                color="primary"
              />
              <SummaryCard
                title="CTR"
                value={`${(emailData.summary.clickToOpenRate * 100).toFixed(1)}%`}
                color="success"
              />
            </div>

            {/* Sequence Performance */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-heading text-xl font-bold text-gray-900 mb-4">
                Эффективность последовательностей
              </h3>
              <div className="space-y-4">
                {emailData.sequencePerformance.map((seq: any, index: number) => (
                  <div key={index} className="border-b border-gray-200 pb-4 last:border-0">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-gray-900">{seq.name}</span>
                      <span className="text-sm text-gray-600">
                        {seq.sent} отправлено
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Open Rate:</span>
                        <span className="ml-2 font-semibold text-emerald-600">
                          {(seq.openRate * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Click Rate:</span>
                        <span className="ml-2 font-semibold text-sky-600">
                          {(seq.clickRate * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Завершено:</span>
                        <span className="ml-2 font-semibold text-gray-900">
                          {(seq.completionRate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Daily Performance */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-heading text-xl font-bold text-gray-900 mb-4">
                Производительность по дням
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={emailData.dailyPerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="sent"
                    stroke={COLORS.primary}
                    name="Отправлено"
                  />
                  <Line
                    type="monotone"
                    dataKey="opened"
                    stroke={COLORS.success}
                    name="Открыто"
                  />
                  <Line
                    type="monotone"
                    dataKey="clicked"
                    stroke={COLORS.warm}
                    name="Кликнуто"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}

        {/* Queue Stats */}
        {activeTab === "queue" && queueData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
              <SummaryCard
                title="В ожидании"
                value={queueData.waiting}
                color="warm"
              />
              <SummaryCard
                title="Активные"
                value={queueData.active}
                color="success"
              />
              <SummaryCard
                title="Отложенные"
                value={queueData.delayed}
                color="primary"
              />
              <SummaryCard
                title="Завершённые"
                value={queueData.completed}
                color="success"
              />
              <SummaryCard
                title="Ошибки"
                value={queueData.failed}
                color="hot"
              />
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

const STAT_CARD_COLORS = {
  hot: "bg-red-50 text-red-600 border-red-200",
  warm: "bg-amber-50 text-amber-600 border-amber-200",
  cold: "bg-blue-50 text-blue-600 border-blue-200",
  primary: "bg-sky-50 text-sky-600 border-sky-200",
  success: "bg-emerald-50 text-emerald-600 border-emerald-200",
};

// Summary Card Component
function SummaryCard({
  title,
  value,
  color,
}: {
  title: string;
  value: string | number;
  color: keyof typeof STAT_CARD_COLORS;
}) {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100">
      <p className="text-sm font-semibold text-gray-600 mb-2">{title}</p>
      <p className={cn("text-3xl font-bold", STAT_CARD_COLORS[color].split(" ")[1])}>
        {value}
      </p>
    </div>
  );
}
