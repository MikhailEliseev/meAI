import type { Metadata } from "next";
import { CaseStudies } from "@/components/landing/CaseStudies";
import { Testimonials } from "@/components/landing/Testimonials";

export const metadata: Metadata = {
  title: "Кейсы клиентов | AIM Agency",
  description:
    "Результаты AI-маркетинга для медицинских клиник. 50+ успешных проектов: рост трафика до 300%, снижение стоимости лида до 70%.",
  keywords: [
    "кейсы медицинского маркетинга",
    "результаты SEO для клиник",
    "маркетинговые кейсы стоматология",
  ],
  openGraph: {
    title: "Кейсы клиентов — AIM Agency",
    description:
      "50+ успешных проектов AI-маркетинга для медицинских клиник. Реальные результаты.",
  },
};

export default function CaseStudiesPage() {
  return (
    <main className="min-h-screen">
      <section className="py-16 md:py-24 px-4 bg-gradient-to-br from-primary-50 via-white to-primary-100">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="font-heading text-3xl md:text-5xl font-bold text-gray-900 mb-4">
            Кейсы наших клиентов
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            50+ медицинских клиник уже доверили нам свой маркетинг. Вот их
            результаты.
          </p>
        </div>
      </section>
      <CaseStudies />
      <Testimonials />
    </main>
  );
}
