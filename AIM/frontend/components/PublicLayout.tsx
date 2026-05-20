"use client";

import { usePathname } from "next/navigation";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

const minimalPaths = ["/billing", "/contracts", "/onboarding", "/tasks"];

export function PublicLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMinimal = pathname === "/" || minimalPaths.some((p) => pathname.startsWith(p));

  if (isMinimal) {
    return <>{children}</>;
  }

  return (
    <>
      <Header />
      <div className="h-16" />
      {children}
      <Footer />
    </>
  );
}
