import React from "react";
import { cn } from "@/lib/utils";

interface TrustBadge {
  id: string;
  label: string;
  icon: string;
  description: string;
}

// Russian Market Adaptation: Используем российские сертификации вместо HIPAA
const badges: TrustBadge[] = [
  {
    id: "fz152",
    label: "ФЗ-152",
    icon: "🔒",
    description: "Соответствие ФЗ-152 о персональных данных",
  },
  {
    id: "yandex",
    label: "Яндекс Партнёр",
    icon: "🎯",
    description: "Сертифицированный партнёр Яндекс.Директ",
  },
  {
    id: "clients",
    label: "50+ Клиентов",
    icon: "👥",
    description: "Более 50 медицинских клиник доверяют нам",
  },
  {
    id: "results",
    label: "Гарантия результата",
    icon: "✓",
    description: "Возврат средств при отсутствии результата",
  },
];

interface TrustBadgesProps {
  className?: string;
  variant?: "horizontal" | "vertical";
}

export function TrustBadges({ className, variant = "horizontal" }: TrustBadgesProps) {
  return (
    <div
      className={cn(
        "flex gap-4",
        variant === "horizontal" ? "flex-row flex-wrap" : "flex-col",
        className
      )}
      role="list"
      aria-label="Наши сертификации и достижения"
    >
      {badges.map((badge) => (
        <div
          key={badge.id}
          className={cn(
            "flex items-center gap-3 px-4 py-3 bg-white rounded-lg shadow-sm border border-gray-200",
            "hover:shadow-md transition-shadow duration-200",
            variant === "horizontal" ? "flex-1 min-w-[200px]" : "w-full"
          )}
          role="listitem"
        >
          <span className="text-2xl" aria-hidden="true">
            {badge.icon}
          </span>
          <div className="flex flex-col">
            <span className="font-semibold text-gray-900 text-sm">
              {badge.label}
            </span>
            <span className="text-xs text-gray-600 sr-only">
              {badge.description}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
