import type { Metadata } from "next";
import { Inter, Poppins } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

const poppins = Poppins({
  weight: ["400", "600", "700"],
  subsets: ["latin"],
  variable: "--font-poppins",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AIM Agency - AI-Powered Medical Marketing",
  description: "AI-первое медицинское маркетинговое агентство. Привлечение пациентов с гарантией результата.",
  keywords: ["медицинский маркетинг", "AI маркетинг", "привлечение пациентов", "SEO для клиник"],
  authors: [{ name: "AIM Agency" }],
  openGraph: {
    type: "website",
    locale: "ru_RU",
    url: "https://iamaim.ru",
    siteName: "AIM Agency",
    title: "AIM Agency - AI-Powered Medical Marketing",
    description: "AI-первое медицинское маркетинговое агентство",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "AIM Agency",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "AIM Agency - AI-Powered Medical Marketing",
    description: "AI-первое медицинское маркетинговое агентство",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className={`${inter.variable} ${poppins.variable}`}>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
