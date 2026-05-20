import type { Metadata } from "next";
import Link from "next/link";
import { TrustBadges } from "@/components/landing/TrustBadges";

export const metadata: Metadata = {
  title: "О нас | AIM Agency",
  description:
    "AIM Agency — AI-first маркетинговое агентство для медицинских клиник. Команда экспертов, 50+ клиентов, гарантия результата.",
  keywords: [
    "маркетинговое агентство медицинское",
    "AI маркетинг",
    "команда маркетологов",
  ],
  openGraph: {
    title: "О нас — AIM Agency",
    description:
      "AI-first медицинское маркетинговое агентство. Наша миссия, команда и подход.",
  },
};

const team = [
  {
    name: "Михаил Елисеев",
    role: "CEO & Основатель",
    bio: "Medical marketer с 10+ летним опытом. Построил маркетинг для 50+ клиник.",
  },
  {
    name: "AI Architect",
    role: "Стратегический AI",
    bio: "Принимает стратегические решения на основе анализа тысяч факторов рынка.",
  },
  {
    name: "SEO Magister",
    role: "AI SEO-эксперт",
    bio: "Автономный AI-агент, специализирующийся на поисковом продвижении медицинских сайтов.",
  },
  {
    name: "Ads Magister",
    role: "AI Эксперт по рекламе",
    bio: "Автономно управляет рекламными кампаниями в Яндекс.Директ и соцсетях.",
  },
  {
    name: "Content Magister",
    role: "AI Контент-стратег",
    bio: "Создаёт и оптимизирует медицинский контент, который ранжируется и конвертирует.",
  },
  {
    name: "Analytics Magister",
    role: "AI Аналитик",
    bio: "Прогнозирует тренды, находит точки роста, предоставляет данные для решений.",
  },
];

const stats = [
  { value: "50+", label: "Клиник" },
  { value: "15 000+", label: "Новых пациентов" },
  { value: "300%", label: "Средний рост трафика" },
  { value: "450%", label: "ROI в среднем" },
  { value: "24/7", label: "AI мониторинг" },
  { value: "4.9", label: "Средняя оценка" },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="py-16 md:py-24 px-4 bg-canvas">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-3xl md:text-5xl font-bold text-ink mb-4">
                Мы — AIM Agency
              </h1>
              <p className="text-lg text-text-muted mb-6 leading-relaxed">
                AI-first маркетинговое агентство для медицинских клиник.
                Мы объединили 10+ лет опыта в медицинском маркетинге с мощью
                искусственного интеллекта, чтобы давать результаты, которые
                конкуренты не могут повторить.
              </p>
              <TrustBadges className="justify-start" />
            </div>
            <div className="grid grid-cols-3 gap-4">
              {stats.map((s) => (
                <div
                  key={s.label}
                  className="bg-surface-2 p-4 rounded-md border border-border-hairline text-center"
                >
                  <div className="text-2xl font-bold text-accent">
                    {s.value}
                  </div>
                  <div className="text-xs text-text-subtle mt-1">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-ink mb-4">
            Наша миссия
          </h2>
          <p className="text-lg text-text-muted leading-relaxed">
            Сделать AI-маркетинг доступным для каждой медицинской клиники в
            России. Мы верим, что искусственный интеллект может работать 24/7,
            находя точки роста, которые человек пропустит. Наша цель — чтобы
            каждая клиника получала пациентов, не переплачивая за рекламу.
          </p>
        </div>
      </section>

      {/* Team */}
      <section className="py-16 px-4 bg-surface-1">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-ink text-center mb-12">
            Наша команда
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {team.map((member) => (
              <div
                key={member.name}
                className="bg-surface-2 rounded-md p-6 border border-border-hairline text-center"
              >
                <div className="w-16 h-16 bg-surface-3 text-accent rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                  {member.name[0]}
                </div>
                <h3 className="font-bold text-ink">
                  {member.name}
                </h3>
                <p className="text-sm text-accent font-medium mb-3">
                  {member.role}
                </p>
                <p className="text-sm text-text-muted">{member.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 text-center">
        <h2 className="text-2xl md:text-3xl font-bold text-ink mb-4">
          Готовы расти вместе с нами?
        </h2>
        <p className="text-text-muted mb-8">
          Оставьте заявку и получите бесплатный аудит вашего маркетинга.
        </p>
        <Link href="/contact" className="btn-primary text-lg px-8 py-4 inline-block">
          Получить консультацию
        </Link>
      </section>
    </main>
  );
}
