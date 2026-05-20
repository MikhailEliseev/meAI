import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
import { PublicLayout } from "@/components/PublicLayout";
import { UTMCapture } from "@/components/UTMCapture";
import { CookieConsent } from "@/components/CookieConsent";
import { YandexMetrika } from "@/components/YandexMetrika";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AIM Agency — AI-маркетинг для медицинских клиник | Гарантия результата",
  description:
    "Привлекаем пациентов с помощью искусственного интеллекта. Увеличение потока пациентов на 30%+ за 3 месяца. Гарантия результата или возврат денег. Работаем с 50+ клиниками по всей России.",
  keywords: [
    "медицинский маркетинг",
    "AI маркетинг для клиник",
    "привлечение пациентов",
    "SEO для медицинских клиник",
    "Яндекс.Директ для клиник",
    "маркетинг для стоматологии",
    "маркетинг для косметологии",
    "реклама медицинских услуг",
    "AI оптимизация рекламы",
    "гарантия результата маркетинг",
  ],
  authors: [{ name: "AIM Agency", url: "https://iamaim.ru" }],
  creator: "AIM Agency",
  publisher: "AIM Agency",
  metadataBase: new URL("https://iamaim.ru"),
  alternates: {
    canonical: "https://iamaim.ru",
  },
  openGraph: {
    type: "website",
    locale: "ru_RU",
    url: "https://iamaim.ru",
    siteName: "AIM Agency",
    title: "AIM Agency — AI-маркетинг для медицинских клиник",
    description:
      "Привлекаем пациентов с помощью искусственного интеллекта. Гарантия результата или возврат денег. 50+ клиник, 15K+ новых пациентов, ROI 450%.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "AIM Agency — AI-маркетинг для медицинских клиник",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "AIM Agency — AI-маркетинг для медицинских клиник",
    description: "Привлекаем пациентов с помощью искусственного интеллекта. Гарантия результата.",
    images: ["/og-image.png"],
    creator: "@aimagency",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    yandex: process.env.NEXT_PUBLIC_YANDEX_VERIFICATION,
    google: process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className={inter.variable}>
      <head>
        {/* Preconnect for performance */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="preconnect" href="https://mc.yandex.ru" />

        {/* Favicon */}
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />

        {/* Structured Data — Organization (single source of truth) */}
        <Script
          id="structured-data-organization"
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              name: "AIM Agency",
              alternateName: "AI Medical Marketing Agency",
              url: "https://iamaim.ru",
              logo: "https://iamaim.ru/logo.png",
              description:
                "AI-первое медицинское маркетинговое агентство в России",
              address: {
                "@type": "PostalAddress",
                addressCountry: "RU",
                addressLocality: "Москва",
              },
              contactPoint: {
                "@type": "ContactPoint",
                telephone: "+7-999-123-45-67",
                contactType: "customer service",
                availableLanguage: ["Russian"],
              },
              sameAs: [
                "https://vk.com/aimagency",
                "https://t.me/aimagency",
              ],
              aggregateRating: {
                "@type": "AggregateRating",
                ratingValue: "4.9",
                reviewCount: "50",
              },
            }),
          }}
        />

        {/* Structured Data — WebSite */}
        <Script
          id="structured-data-website"
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebSite",
              name: "AIM Agency",
              url: "https://iamaim.ru",
              potentialAction: {
                "@type": "SearchAction",
                target:
                  "https://iamaim.ru/search?q={search_term_string}",
                "query-input": "required name=search_term_string",
              },
            }),
          }}
        />

        {/* Structured Data — BreadcrumbList */}
        <Script
          id="structured-data-breadcrumb"
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "BreadcrumbList",
              itemListElement: [
                {
                  "@type": "ListItem",
                  position: 1,
                  name: "Главная",
                  item: "https://iamaim.ru",
                },
              ],
            }),
          }}
        />
      </head>
      <body className={inter.className}>
        <PublicLayout>
          {children}
        </PublicLayout>
        <CookieConsent />
        <YandexMetrika />
        <UTMCapture />
      </body>
    </html>
  );
}
