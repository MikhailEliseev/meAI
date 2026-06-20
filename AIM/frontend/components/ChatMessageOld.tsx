'use client';

import { motion } from 'framer-motion';
import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import { cn } from '@/lib/utils';

interface ChatMessageOldProps {
  role: 'user' | 'agent';
  content: string;
  timestamp?: Date;
}

function ChatMessageOldComponent({ role, content, timestamp }: ChatMessageOldProps) {
  const isAgent = role === 'agent';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'flex gap-3 max-w-[85%]',
        isAgent ? 'self-start' : 'self-end flex-row-reverse'
      )}
    >
      <div
        className={cn(
          'w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold',
          isAgent ? 'bg-accent text-white' : 'bg-surface-3 text-text-muted'
        )}
      >
        {isAgent ? 'AI' : 'Вы'}
      </div>

      <div
        className={cn(
          'rounded-lg px-4 py-3 text-sm leading-relaxed min-w-0 overflow-hidden',
          isAgent
            ? 'bg-surface-2 border border-border-hairline text-ink'
            : 'bg-accent text-white'
        )}
      >
        {isAgent ? (
          <div className="prose prose-sm prose-invert max-w-none [&_table]:text-xs [&_th]:text-xs [&_td]:text-xs [&_pre]:text-xs [&_strong]:text-ink [&_em]:text-text-muted [&_h2]:text-ink [&_h3]:text-ink [&_p]:text-ink/90 [&_li]:text-ink/90 [&_hr]:border-border-hairline">
            {content ? (
              <ReactMarkdown>{content}</ReactMarkdown>
            ) : (
              <span className="inline-flex gap-1">
                <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            )}
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{content}</p>
        )}

        {timestamp && (
          <span className="block text-xs mt-1 opacity-50">
            {timestamp.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>
    </motion.div>
  );
}

export const ChatMessageOld = memo(ChatMessageOldComponent, (prev, next) => {
  return prev.content === next.content;
});

ChatMessageOld.displayName = 'ChatMessageOld';
