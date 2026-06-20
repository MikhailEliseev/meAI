'use client';

import { useRef, useEffect, memo } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { EmptyState } from './EmptyState';
import { cn } from '@/lib/utils';
import { useChatStream } from '@/hooks/useChatStream';

function SalesChatComponent({ className }: { className?: string }) {
  const { messages, sendMessage, stop, status, streamingRef } = useChatStream();
  const scrollRef = useRef<HTMLDivElement>(null);
  const isStreaming = status === 'streaming' || status === 'submitted';
  const hasMessages = messages.length > 0;

  // Smooth scroll only when NOT streaming (final message sync)
  useEffect(() => {
    if (!isStreaming) {
      scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isStreaming]);

  return (
    <section
      className={cn('relative flex flex-col h-screen bg-canvas', className)}
      aria-labelledby="chat-heading"
    >
      <header className="flex items-center justify-between px-6 py-3 border-b border-border-hairline bg-canvas/80 backdrop-blur sticky top-0 z-10 h-14 shrink-0">
        <a href="/" className="flex items-center gap-2 font-bold text-lg text-ink no-underline">
          <span className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
            <span className="text-white font-bold text-xs">AI</span>
          </span>
          AIM
        </a>
        <a href="/about" className="text-sm text-text-muted hover:text-ink transition-colors">
          О компании
        </a>
      </header>

      {hasMessages ? (
        <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4 max-w-3xl mx-auto w-full">
          {messages.map((message, index) => {
              const isLastAgentMessage = message.role === 'agent' && index === messages.length - 1;
              return (
                <ChatMessage
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  timestamp={message.timestamp}
                  isStreaming={isLastAgentMessage && isStreaming}
                  contentRef={isLastAgentMessage && isStreaming ? streamingRef : undefined}
                />
              );
            })}

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

export const SalesChat = memo(SalesChatComponent);
SalesChat.displayName = 'SalesChat';
