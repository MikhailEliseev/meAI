import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Блог | AIM Agency",
  description:
    "Блог о медицинском маркетинге, AI-технологиях, SEO и рекламе. Статьи, исследования и гайды для маркетологов медицинских клиник.",
  keywords: [
    "блог медицинского маркетинга",
    "статьи о SEO для клиник",
    "AI маркетинг статьи",
  ],
};

export default function BlogPage() {
  return (
    <main className="min-h-screen">
      <section className="py-16 md:py-24 px-4 bg-gradient-to-br from-primary-50 via-white to-primary-100">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="font-heading text-3xl md:text-5xl font-bold text-gray-900 mb-4">
            Блог
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Статьи, исследования и гайды о медицинском маркетинге и AI.
          </p>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <div className="text-6xl mb-6">📝</div>
          <h2 className="font-heading text-2xl font-bold text-gray-900 mb-4">
            Скоро здесь появятся статьи
          </h2>
          <p className="text-gray-600 mb-8 leading-relaxed">
            Наша команда AI-агентов готовит первые материалы. Мы будем
            публиковать исследования рынка, гайды по SEO для медицинских
            сайтов, кейсы и аналитику трендов.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/contact" className="btn-primary">
              Подписаться на обновления
            </Link>
            <Link href="/case-studies" className="btn-secondary">
              Посмотреть кейсы
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
