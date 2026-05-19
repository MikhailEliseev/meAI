"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

type ConsentPreferences = {
  necessary: boolean;
  analytics: boolean;
  marketing: boolean;
};

const STORAGE_KEY = "aim_cookie_consent";
const CONSENT_EVENT = "aimConsentChanged";

function getStoredConsent(): ConsentPreferences | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return null;
}

function storeConsent(prefs: ConsentPreferences) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch {}
}

function dispatchConsentEvent(prefs: ConsentPreferences) {
  try {
    window.dispatchEvent(
      new CustomEvent(CONSENT_EVENT, { detail: prefs })
    );
  } catch {}
}

export function useCookieConsent(): ConsentPreferences | null {
  const [consent, setConsent] = useState<ConsentPreferences | null>(getStoredConsent);

  useEffect(() => {
    const stored = getStoredConsent();
    if (stored) {
      setConsent(stored);
      return;
    }

    const handler = (e: Event) => {
      setConsent((e as CustomEvent).detail);
    };
    window.addEventListener(CONSENT_EVENT, handler);
    return () => window.removeEventListener(CONSENT_EVENT, handler);
  }, []);

  return consent;
}

export function CookieConsent() {
  const [show, setShow] = useState(false);
  const [preferences, setPreferences] = useState<ConsentPreferences>({
    necessary: true,
    analytics: true,
    marketing: false,
  });

  useEffect(() => {
    if (!getStoredConsent()) {
      const timer = setTimeout(() => setShow(true), 400);
      return () => clearTimeout(timer);
    }
  }, []);

  const acceptAll = useCallback(() => {
    const prefs: ConsentPreferences = {
      necessary: true,
      analytics: true,
      marketing: true,
    };
    storeConsent(prefs);
    dispatchConsentEvent(prefs);
    setShow(false);
  }, []);

  const acceptSelected = useCallback(() => {
    storeConsent(preferences);
    dispatchConsentEvent(preferences);
    setShow(false);
  }, [preferences]);

  const declineAll = useCallback(() => {
    const prefs: ConsentPreferences = {
      necessary: true,
      analytics: false,
      marketing: false,
    };
    storeConsent(prefs);
    dispatchConsentEvent(prefs);
    setShow(false);
  }, []);

  const toggle = (key: keyof ConsentPreferences) => {
    if (key === "necessary") return;
    setPreferences((p) => ({ ...p, [key]: !p[key] }));
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ y: "100%", opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: "100%", opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6"
        >
          <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-2xl border border-gray-200 p-6 space-y-4">
            {/* Title */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-heading text-lg font-bold text-gray-900">
                  Мы используем cookie-файлы
                </h3>
                <p className="mt-2 text-sm text-gray-600 leading-relaxed">
                  Это помогает нам анализировать трафик и улучшать сайт.
                  Подробнее — в{" "}
                  <a
                    href="/privacy-policy"
                    className="text-primary-600 hover:text-primary-700 underline"
                  >
                    Политике конфиденциальности
                  </a>
                  . Обработка данных — в соответствии с ФЗ-152.
                </p>
              </div>
            </div>

            {/* Preferences toggles */}
            <div className="space-y-2 border-y border-gray-100 py-3">
              <label className="flex items-center gap-3 cursor-not-allowed opacity-70">
                <input
                  type="checkbox"
                  checked={preferences.necessary}
                  disabled
                  className="w-4 h-4 rounded border-gray-300 text-primary-600 accent-primary-600"
                />
                <div>
                  <span className="text-sm font-semibold text-gray-700">
                    Необходимые
                  </span>
                  <span className="text-xs text-gray-500 ml-2">
                    Всегда включены
                  </span>
                  <p className="text-xs text-gray-500">
                    Базовая функциональность сайта
                  </p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.analytics}
                  onChange={() => toggle("analytics")}
                  className="w-4 h-4 rounded border-gray-300 text-primary-600 accent-primary-600"
                />
                <div>
                  <span className="text-sm font-semibold text-gray-700">
                    Аналитика
                  </span>
                  <p className="text-xs text-gray-500">
                    Яндекс.Метрика — помогает понять, как используют сайт
                  </p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.marketing}
                  onChange={() => toggle("marketing")}
                  className="w-4 h-4 rounded border-gray-300 text-primary-600 accent-primary-600"
                />
                <div>
                  <span className="text-sm font-semibold text-gray-700">
                    Маркетинг
                  </span>
                  <p className="text-xs text-gray-500">
                    VK Pixel и MyTarget — персонализация рекламы
                  </p>
                </div>
              </label>
            </div>

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={acceptAll}
                className="flex-1 btn-primary py-2.5 text-sm"
              >
                Принять все
              </button>
              <button
                onClick={acceptSelected}
                className="flex-1 btn-secondary py-2.5 text-sm"
              >
                Принять выбранные
              </button>
              <button
                onClick={declineAll}
                className="flex-1 px-4 py-2.5 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
              >
                Только необходимые
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
