'use client';

import { SalesChatOld } from '@/components/SalesChatOld';

export default function ChatOldPage() {
  return (
    <main className="h-screen flex flex-col bg-canvas">
      <div className="flex items-center justify-center gap-4 py-2 bg-red-50/10 border-b border-red-500/30 shrink-0">
        <span className="text-sm font-bold text-red-500">OLD — React state every text-delta</span>
        <a
          href="/chat-new"
          target="_blank"
          className="text-xs px-3 py-1 rounded bg-surface-2 border border-border-hairline hover:bg-surface-3 transition-colors text-ink no-underline"
        >
          Открыть NEW версию
        </a>
      </div>
      <div className="flex-1 min-h-0">
        <SalesChatOld />
      </div>
    </main>
  );
}
