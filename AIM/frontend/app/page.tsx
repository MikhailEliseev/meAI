import { HeroSection } from "@/components/landing/HeroSection";
import { CaseStudies } from "@/components/landing/CaseStudies";
import { Testimonials } from "@/components/landing/Testimonials";
import { Awards } from "@/components/landing/Awards";
import { ProcessSteps } from "@/components/landing/ProcessSteps";
import { FAQ } from "@/components/landing/FAQ";
import { ContactForm } from "@/components/landing/ContactForm";

export default function Home() {
  return (
    <main className="min-h-screen">
      <HeroSection />
      <ProcessSteps />
      <CaseStudies limit={3} />
      <Testimonials limit={3} />
      <Awards />
      <FAQ />
      <ContactForm />
    </main>
  );
}
