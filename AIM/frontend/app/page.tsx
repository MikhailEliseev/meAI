'use client';

import { SalesChat } from '@/components/SalesChat';

export default function HomePage() {
  return (
    <main className="h-screen flex flex-col">
      {/* Test buttons */}
      <div className="flex items-center justify-center gap-4 py-3 bg-amber-50/10 border-b border-amber-500/20 shrink-0">
        <span className="text-xs text-text-muted mr-2">Тест чата:</span>
        <a
          href="/chat-test"
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-1.5 text-sm rounded-md bg-surface-2 border border-border-hairline hover:bg-surface-3 transition-colors text-ink no-underline inline-block"
        >
          Открыть тест-страницу (Old vs New)
        </a>
      </div>

      <div className="flex-1 min-h-0">
        <SalesChat />
      </div>
    </main>
  );
}
