import dynamic from "next/dynamic";
import { HeroSection } from "@/components/landing/HeroSection";
import { SalesChat } from "@/components/landing/SalesChat";
import { ProcessSteps } from "@/components/landing/ProcessSteps";

const CaseStudies = dynamic(
  () => import("@/components/landing/CaseStudies").then((m) => ({ default: m.CaseStudies })),
  { loading: () => <SectionSkeleton /> }
);
const Testimonials = dynamic(
  () =>
    import("@/components/landing/Testimonials").then((m) => ({
      default: m.Testimonials,
    })),
  { loading: () => <SectionSkeleton /> }
);
const Awards = dynamic(
  () => import("@/components/landing/Awards").then((m) => ({ default: m.Awards })),
  { loading: () => <SectionSkeleton height="h-80" /> }
);
const FAQ = dynamic(
  () => import("@/components/landing/FAQ").then((m) => ({ default: m.FAQ })),
  { loading: () => <SectionSkeleton height="h-[600px]" /> }
);
const ContactForm = dynamic(
  () =>
    import("@/components/landing/ContactForm").then((m) => ({
      default: m.ContactForm,
    })),
  { loading: () => <SectionSkeleton height="h-[700px]" /> }
);

function SectionSkeleton({ height = "h-96" }: { height?: string }) {
  return (
    <section className={`py-20 px-4 ${height} bg-gray-50 animate-pulse`}>
      <div className="max-w-7xl mx-auto">
        <div className="h-8 bg-gray-200 rounded w-1/3 mx-auto mb-4" />
        <div className="h-4 bg-gray-200 rounded w-2/3 mx-auto" />
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen">
      <SalesChat />
      <HeroSection className="min-h-0 py-20" />
      <ProcessSteps />
      <CaseStudies limit={3} />
      <Testimonials limit={3} />
      <Awards />
      <FAQ />
      <ContactForm />
    </main>
  );
}
