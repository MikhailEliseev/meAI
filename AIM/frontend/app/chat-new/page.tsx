'use client';

import { SalesChat } from '@/components/SalesChat';

export default function ChatNewPage() {
  return (
    <main className="h-screen flex flex-col bg-canvas">
      <div className="flex items-center justify-center gap-4 py-2 bg-green-50/10 border-b border-green-500/30 shrink-0">
        <span className="text-sm font-bold text-green-500">NEW — Direct DOM via streamingRef</span>
        <a
          href="/chat-old"
          target="_blank"
          className="text-xs px-3 py-1 rounded bg-surface-2 border border-border-hairline hover:bg-surface-3 transition-colors text-ink no-underline"
        >
          Открыть OLD версию
        </a>
      </div>
      <div className="flex-1 min-h-0">
        <SalesChat />
      </div>
    </main>
  );
}
