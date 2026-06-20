'use client';

import { SalesChatOld } from '@/components/SalesChatOld';
import { SalesChat } from '@/components/SalesChat';

export default function ChatTestPage() {
  return (
    <main className="h-screen flex flex-col bg-canvas">
      <div className="flex-1 flex flex-row min-h-0">
        {/* OLD — React state on every text-delta */}
        <div className="flex-1 border-r-2 border-red-500/30 min-w-0">
          <SalesChatOld />
        </div>

        {/* NEW — Direct DOM via streamingRef, no progress */}
        <div className="flex-1 border-l-2 border-green-500/30 min-w-0">
          <SalesChat />
        </div>
      </div>
    </main>
  );
}
