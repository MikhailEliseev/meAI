import { DashboardNav } from "@/components/DashboardNav";

export const dynamic = "force-dynamic";

export const metadata = {
  title: {
    default: "Дашборд | AIM Agency",
    template: "%s | AIM Agency",
  },
  robots: {
    index: false,
    follow: false,
  },
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex">
      <DashboardNav />
      <main className="flex-1 min-h-[calc(100vh-4rem)] bg-surface-1">
        {children}
      </main>
    </div>
  );
}
