'use client';

import { useRef, useEffect, memo } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { EmptyState } from './EmptyState';
import { cn } from '@/lib/utils';
import { useChatStream } from '@/hooks/useChatStream';

function SalesChatComponent({ className }: { className?: string }) {
  const { messages, sendMessage, stop, reset, status, streamingRef } = useChatStream();
  const scrollRef = useRef<HTMLDivElement>(null);
  const isStreaming = status === 'streaming' || status === 'submitted';
  const hasMessages = messages.length > 0;

  const lastMessage = messages[messages.length - 1];
  const showThinkingStatus = (status === 'submitted' || status === 'streaming') &&
                             lastMessage?.role === 'agent' &&
                             lastMessage.content === '';

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
        <div className="flex items-center gap-3">
          {hasMessages && (
            <button
              onClick={reset}
              disabled={isStreaming}
              className="text-sm text-text-muted hover:text-ink transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
              aria-label="Начать новый чат"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 8h12M8 2l6 6-6 6" />
              </svg>
              Новый чат
            </button>
          )}
          <a href="/about" className="text-sm text-text-muted hover:text-ink transition-colors">
            О компании
          </a>
        </div>
      </header>

      {hasMessages ? (
        <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4 max-w-3xl mx-auto w-full">
          {messages.map((message, index) => {
              const isLastAgentMessage = message.role === 'agent' && index === messages.length - 1;
              const shouldHideEmpty = isLastAgentMessage && showThinkingStatus;

              if (shouldHideEmpty) return null;

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

          {showThinkingStatus && (
            <div className="flex gap-3 max-w-[85%] self-start">
              <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold bg-accent text-white">
                AI
              </div>
              <div className="rounded-lg px-4 py-3 text-sm bg-surface-2 border border-border-hairline text-ink flex items-center gap-2">
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </span>
                <span className="text-text-muted">Анализирую запрос...</span>
              </div>
            </div>
          )}

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
