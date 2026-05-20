"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/services", label: "Услуги" },
  { href: "/case-studies", label: "Кейсы" },
  { href: "/about", label: "О нас" },
  { href: "/blog", label: "Блог" },
  { href: "/contact", label: "Контакты" },
];

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-40 bg-canvas/80 backdrop-blur-md border-b border-border-hairline"
        role="banner"
      >
        <nav
          className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between"
          aria-label="Основная навигация"
        >
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 text-xl font-bold text-ink hover:text-accent transition-colors"
            aria-label="AIM Agency — на главную"
          >
            <span className="w-8 h-8 bg-accent text-white rounded-md flex items-center justify-center text-sm font-extrabold">
              AIM
            </span>
            <span className="hidden sm:inline">AIM Agency</span>
          </Link>

          {/* Desktop nav */}
          <ul className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={cn(
                    "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                    pathname === link.href
                      ? "text-accent bg-surface-3"
                      : "text-text-muted hover:text-ink hover:bg-surface-2"
                  )}
                >
                  {link.label}
                </Link>
              </li>
            ))}
            <li className="ml-3">
              <Link
                href="/contact"
                className="btn-primary text-sm py-2 px-5"
              >
                Бесплатный аудит
              </Link>
            </li>
          </ul>

          {/* Mobile burger */}
          <button
            onClick={() => setMobileOpen((o) => !o)}
            className="md:hidden p-2 rounded-md text-text-muted hover:bg-surface-2 transition-colors"
            aria-label={mobileOpen ? "Закрыть меню" : "Открыть меню"}
            aria-expanded={mobileOpen}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              {mobileOpen ? (
                <>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </>
              ) : (
                <>
                  <line x1="4" y1="6" x2="20" y2="6" />
                  <line x1="4" y1="12" x2="20" y2="12" />
                  <line x1="4" y1="18" x2="20" y2="18" />
                </>
              )}
            </svg>
          </button>
        </nav>
      </header>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-30 md:hidden"
          >
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
              onClick={() => setMobileOpen(false)}
            />

            {/* Drawer */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="absolute right-0 top-0 bottom-0 w-72 bg-canvas border-l border-border-hairline pt-20 px-6"
            >
              <ul className="space-y-1">
                {navLinks.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      onClick={() => setMobileOpen(false)}
                      className={cn(
                        "block px-4 py-3 rounded-lg text-base font-medium transition-colors",
                        pathname === link.href
                          ? "text-accent bg-surface-3"
                          : "text-text-muted hover:bg-surface-2"
                      )}
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
                <li className="pt-3">
                  <Link
                    href="/contact"
                    onClick={() => setMobileOpen(false)}
                    className="btn-primary block text-center py-3"
                  >
                    Бесплатный аудит
                  </Link>
                </li>
              </ul>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
