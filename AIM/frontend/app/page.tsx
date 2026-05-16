import { HeroSection } from "@/components/landing/HeroSection";

export default function Home() {
  return (
    <main className="min-h-screen">
      <HeroSection />
      {/* Placeholder for other sections */}
      <div id="case-studies" className="scroll-mt-20" />
      <div id="contact-form" className="scroll-mt-20" />
    </main>
  );
}
