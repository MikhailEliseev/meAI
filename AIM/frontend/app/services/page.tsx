import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Услуги AI-маркетинга | AIM Agency",
  description:
    "SEO, Яндекс.Директ, контент-маркетинг и AI-аналитика для медицинских клиник. Комплексное продвижение с гарантией результата.",
  keywords: [
    "услуги маркетинга для клиник",
    "SEO для медицинских сайтов",
    "Яндекс.Директ клиники",
    "AI-аналитика маркетинга",
  ],
  openGraph: {
    title: "Услуги AI-маркетинга — AIM Agency",
    description:
      "Полный спектр маркетинговых услуг для медицинских клиник с применением AI.",
  },
};

const services = [
  {
    id: "seo",
    icon: "🔍",
    title: "SEO-продвижение",
    subtitle: "Рост органического трафика",
    price: "от ₽80 000/мес",
    features: [
      "AI-анализ 200+ факторов ранжирования",
      "Технический аудит и оптимизация",
      "Создание E-E-A-T контента",
      "Ежемесячная отчётность",
      "Мониторинг позиций 24/7",
    ],
  },
  {
    id: "ads",
    icon: "📢",
    title: "Яндекс.Директ",
    subtitle: "Контекстная и таргетированная реклама",
    price: "от ₽60 000/мес + бюджет",
    features: [
      "AI-оптимизация ставок",
      "A/B тестирование объявлений",
      "Геотаргетинг и ретаргетинг",
      "Настройка целей в Метрике",
      "Еженедельная оптимизация кампаний",
    ],
  },
  {
    id: "content",
    icon: "✍️",
    title: "Контент-маркетинг",
    subtitle: "Статьи, кейсы, соцсети",
    price: "от ₽50 000/мес",
    features: [
      "AI-генерация медицинского контента",
      "SEO-оптимизация текстов",
      "Ведение блога и соцсетей",
      "Создание видео-контента",
      "Контент-план на месяц вперёд",
    ],
  },
  {
    id: "analytics",
    icon: "📊",
    title: "AI-аналитика",
    subtitle: "Данные для роста",
    price: "от ₽40 000/мес",
    features: [
      "Прогнозирование трафика и конверсий",
      "Анализ конкурентов в реальном времени",
      "Дашборды в Grafana",
      "AI Lead Scoring (30+ факторов)",
      "Автоматическая отчётность",
    ],
  },
  {
    id: "full",
    icon: "🚀",
    title: "Полное сопровождение",
    subtitle: "Комплексный маркетинг под ключ",
    price: "от ₽180 000/мес",
    features: [
      "SEO + Директ + Контент + Аналитика",
      "Персональный менеджер",
      "Еженедельные созвоны",
      "Гарантия результата или возврат",
      "Приоритетная поддержка 24/7",
    ],
    highlighted: true,
  },
];

export default function ServicesPage() {
  return (
    <main className="min-h-screen">
      <section className="py-16 md:py-24 px-4 bg-canvas">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-3xl md:text-5xl font-bold text-ink mb-4">
            Услуги AI-маркетинга
          </h1>
          <p className="text-lg text-text-muted max-w-2xl mx-auto">
            Полный спектр маркетинговых услуг с применением искусственного
            интеллекта для медицинских клиник.
          </p>
        </div>
      </section>

      <section className="py-16 px-4" id="services-grid">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((service) => (
              <div
                key={service.id}
                className={`relative rounded-lg border p-8 flex flex-col ${
                  service.highlighted
                    ? "border-accent bg-surface-3 scale-[1.02]"
                    : "border-border-hairline bg-surface-2"
                } transition-all duration-300`}
              >
                {service.highlighted && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-white text-xs font-bold px-4 py-1 rounded-md">
                    Рекомендуем
                  </span>
                )}
                <div className="text-4xl mb-4">{service.icon}</div>
                <h3 className="text-xl font-bold text-ink mb-1">
                  {service.title}
                </h3>
                <p className="text-sm text-text-subtle mb-4">
                  {service.subtitle}
                </p>
                <p className="text-2xl font-bold text-accent mb-6">
                  {service.price}
                </p>
                <ul className="space-y-2 mb-8 flex-1">
                  {service.features.map((f) => (
                    <li
                      key={f}
                      className="flex items-start gap-2 text-sm text-text-muted"
                    >
                      <span className="text-accent mt-0.5">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/contact"
                  className={`block text-center py-3 rounded-lg font-semibold transition-colors ${
                    service.highlighted
                      ? "btn-primary"
                      : "btn-secondary"
                  }`}
                >
                  Заказать
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
