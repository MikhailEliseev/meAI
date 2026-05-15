"use client";

import { useNotifications } from "@/hooks/useNotifications";
import { useEffect } from "react";

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { status, isConnected } = useNotifications();

  useEffect(() => {
    console.log('[WebSocket] Status:', status);
  }, [status]);

  return (
    <>
      {children}
      {/* Connection status indicator */}
      <div className="fixed bottom-4 right-4 z-50">
        {status === 'connecting' && (
          <div className="bg-yellow-100 text-yellow-800 px-3 py-2 rounded-lg shadow-lg text-sm flex items-center gap-2">
            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-yellow-800"></div>
            Connecting...
          </div>
        )}
        {status === 'error' && (
          <div className="bg-red-100 text-red-800 px-3 py-2 rounded-lg shadow-lg text-sm flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Connection error
          </div>
        )}
      </div>
    </>
  );
}
