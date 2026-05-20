import { cn } from "@/lib/utils";

type CardElevation = 1 | 2;

interface CardProps {
  elevation?: CardElevation;
  className?: string;
  children: React.ReactNode;
}

const elevationStyles: Record<CardElevation, string> = {
  1: "bg-surface-2 border border-border-hairline",
  2: "bg-surface-3 border border-border-strong",
};

export function Card({ elevation = 1, className, children }: CardProps) {
  return (
    <div className={cn("rounded-lg", elevationStyles[elevation], className)}>
      {children}
    </div>
  );
}
