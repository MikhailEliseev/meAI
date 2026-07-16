import React, { memo } from 'react';

function ChatBubbleComponent({ role, content, timestamp, isStreaming, contentRef }) {
  const isAgent = role === 'agent';
  const isEmpty = !content || !content.trim();

  return (
    <div className={'flex gap-3 max-w-[85%] ' + (isAgent ? 'self-start' : 'self-end flex-row-reverse')}>
      <div className={'w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold ' + (isAgent ? 'bg-accent text-white' : 'bg-surface-3 text-text-muted')}>
        {isAgent ? 'AI' : 'Вы'}
      </div>
      <div className={'rounded-lg px-4 py-3 text-sm leading-relaxed min-w-0 overflow-hidden ' + (isAgent ? 'bg-surface-2 border border-border-hairline text-ink' : 'bg-accent text-white')}>
        {isAgent ? (
          <div
            className="whitespace-pre-wrap chat-bubble-content"
            data-streaming={isStreaming ? 'true' : 'false'}
          >
            {/* Dedicated streaming target — React NEVER puts children here, RAF writes textContent.
                Visible only during active streaming; hidden when dots or final content show. */}
            <span ref={contentRef} className="stream-target" style={{display: (isEmpty && isStreaming) ? 'inline' : 'none'}} />
            {isEmpty && isStreaming ? (
              <span className="chat-loading-text">
                <span className="chat-loading-label">Пожалуйста, подождите</span>
                <span className="inline-flex gap-1 ml-1">
                  <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
                  <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
                  <span className="w-1.5 h-1.5 bg-accent/70 rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
                </span>
              </span>
            ) : (
              content
            )}
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{content}</p>
        )}
        {timestamp && (
          <span className="block text-xs mt-1 opacity-50">
            {new Date(timestamp).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'})}
          </span>
        )}
      </div>
    </div>
  );
}

export const ChatBubble = memo(ChatBubbleComponent, (prev, next) => {
  return (
    prev.content === next.content &&
    prev.isStreaming === next.isStreaming &&
    prev.timestamp === next.timestamp
  );
});
