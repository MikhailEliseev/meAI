"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <main className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="text-8xl mb-6">🔧</div>
        <h1 className="text-4xl font-bold text-ink mb-3">
          Что-то пошло не так
        </h1>
        <p className="text-lg text-text-muted mb-2">
          Произошла непредвиденная ошибка.
        </p>
        <p className="text-sm text-text-subtle mb-8">
          Наш AI уже в курсе и работает над исправлением. Попробуйте обновить
          страницу.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button onClick={reset} className="btn-primary">
            Попробовать снова
          </button>
          <Link href="/" className="btn-secondary">
            На главную
          </Link>
        </div>
      </div>
    </main>
  );
}
