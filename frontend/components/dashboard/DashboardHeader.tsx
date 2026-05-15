"use client";

import { useState } from "react";

interface DashboardHeaderProps {
  user: {
    name?: string | null;
    tenantId: string;
  };
}

export default function DashboardHeader({ user }: DashboardHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="sticky top-0 z-10 flex-shrink-0 flex h-16 bg-white shadow">
      <button
        type="button"
        className="px-4 border-r border-gray-200 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 lg:hidden"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
      >
        <span className="sr-only">Open sidebar</span>
        <svg
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="1.5"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
          />
        </svg>
      </button>

      <div className="flex-1 px-4 flex justify-between">
        <div className="flex-1 flex items-center">
          <h2 className="text-lg font-semibold text-gray-900">
            Welcome, {user.name}
          </h2>
        </div>

        <div className="ml-4 flex items-center md:ml-6">
          <div className="text-sm text-gray-500">
            Tenant: <span className="font-medium">{user.tenantId}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
