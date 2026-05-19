import type { Metadata } from "next";
import { ContactForm } from "@/components/landing/ContactForm";

export const metadata: Metadata = {
  title: "Контакты | AIM Agency",
  description:
    "Свяжитесь с нами для бесплатной консультации по AI-маркетингу для вашей клиники. Отвечаем в течение 15 минут.",
  keywords: [
    "контакты маркетингового агентства",
    "заказать маркетинг для клиники",
    "бесплатная консультация маркетолога",
  ],
  openGraph: {
    title: "Контакты — AIM Agency",
    description: "Бесплатная консультация по AI-маркетингу для медицинских клиник.",
  },
};

export default function ContactPage() {
  return <ContactForm />;
}
