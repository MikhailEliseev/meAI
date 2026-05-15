"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";

interface DashboardSidebarProps {
  user: {
    name?: string | null;
    email?: string | null;
    tenantId: string;
  };
}

const navigation = [
  { name: "Dashboard", href: "/", icon: "📊" },
  { name: "Projects", href: "/projects", icon: "📁" },
  { name: "Tasks", href: "/tasks", icon: "✓" },
  { name: "Progress", href: "/progress", icon: "📈" },
];

export default function DashboardSidebar({ user }: DashboardSidebarProps) {
  const pathname = usePathname();

  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
      <div className="flex flex-col flex-grow bg-white border-r border-gray-200 pt-5 pb-4 overflow-y-auto">
        <div className="flex items-center flex-shrink-0 px-4">
          <h1 className="text-2xl font-bold text-blue-600">AIM</h1>
        </div>

        <div className="mt-5 flex-1 flex flex-col">
          <nav className="flex-1 px-2 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`
                    group flex items-center px-2 py-2 text-sm font-medium rounded-md
                    ${
                      isActive
                        ? "bg-blue-50 text-blue-600"
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    }
                  `}
                >
                  <span className="mr-3 text-xl">{item.icon}</span>
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
          <div className="flex-shrink-0 w-full group block">
            <div className="flex items-center">
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-700">
                  {user.name}
                </p>
                <p className="text-xs font-medium text-gray-500">
                  {user.email}
                </p>
              </div>
            </div>
            <button
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="mt-3 w-full text-left text-sm text-gray-600 hover:text-gray-900"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
