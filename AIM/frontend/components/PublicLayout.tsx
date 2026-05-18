"use client";

import { usePathname } from "next/navigation";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

const dashboardPaths = ["/billing", "/contracts", "/onboarding", "/tasks"];

export function PublicLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isDashboard = dashboardPaths.some((p) => pathname.startsWith(p));

  if (isDashboard) {
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
