'use client';

import { useRef, useEffect, memo } from 'react';
import { ChatMessageOld } from './ChatMessageOld';
import { ChatInput } from './ChatInput';
import { EmptyState } from './EmptyState';
import { ProgressIndicator } from './ProgressIndicator';
import { cn } from '@/lib/utils';
import { useChatStreamOld } from '@/hooks/useChatStreamOld';

function SalesChatOldComponent({ className }: { className?: string }) {
  const { messages, sendMessage, stop, status, progress } = useChatStreamOld();
  const scrollRef = useRef<HTMLDivElement>(null);
  const isStreaming = status === 'streaming' || status === 'submitted';
  const hasMessages = messages.length > 0;

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, progress]);

  return (
    <section className={cn('relative flex flex-col h-full bg-canvas', className)} aria-labelledby="chat-heading-old">
      <header className="flex items-center px-6 py-2 border-b border-border-hairline bg-red-50/10 shrink-0">
        <span className="text-sm font-bold text-red-500">OLD — React state every text-delta</span>
      </header>

      {hasMessages ? (
        <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4 max-w-3xl mx-auto w-full">
          {messages.map((message) => (
              <ChatMessageOld
                key={message.id}
                role={message.role}
                content={message.content}
                timestamp={message.timestamp}
              />
            ))}

          {progress && <ProgressIndicator progress={progress} />}
          <div ref={scrollRef} />
        </div>
      ) : (
        <EmptyState onSend={sendMessage} />
      )}

      {hasMessages && (
        <div className="sticky bottom-0 bg-canvas border-t border-border-hairline max-w-3xl mx-auto w-full">
          <ChatInput
            onSend={sendMessage}
            onStop={stop}
            isStreaming={isStreaming}
            disabled={!isStreaming && status === 'error'}
          />
        </div>
      )}
    </section>
  );
}

export const SalesChatOld = memo(SalesChatOldComponent);
SalesChatOld.displayName = 'SalesChatOld';
