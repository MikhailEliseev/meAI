import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { useStreamChat } from './useStreamChat.js';
import { ChatBubble } from './components/ChatBubble.jsx';
import { ChatInput } from './components/ChatInput.jsx';
import { EmptyChat } from './components/EmptyChat.jsx';
import { PhaseTracker } from './components/PhaseTracker.jsx';
import { ReportPreview } from './components/ReportPreview.jsx';
import { FallbackForm } from './components/FallbackForm.jsx';

function HermesChat() {
  const { messages, sendMessage, clearMessages, stop, status, streamingRef, phases, reportData, sessionId } = useStreamChat();
  const [showFallback, setShowFallback] = useState(false);
  const chatEndRef = useRef(null);
  const isStreaming = status === 'streaming' || status === 'submitted';
  const hasMessages = messages.length > 0;

  // Expose methods for WordPress integration
  useEffect(() => {
    window.aimChatSend = (text) => {
      if (typeof text === 'string' && text.trim()) {
        sendMessage(text.trim());
      }
    };
    window.aimChatClear = () => {
      clearMessages();
    };
    return () => {
      delete window.aimChatSend;
      delete window.aimChatClear;
    };
  }, [sendMessage, clearMessages]);

  // Clean up old localStorage keys from vanilla JS chat
  useEffect(() => {
    try {
      const oldKeys = ['hermes_messages', 'hermes_session', 'hermes_sessions'];
      oldKeys.forEach(k => localStorage.removeItem(k));
    } catch {}
  }, []);

  // Smooth scroll only when NOT streaming (final message sync)
  useEffect(() => {
    if (!isStreaming) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isStreaming]);

  // Auto-start session on first load
  useEffect(() => {
    if (!hasMessages && status === 'ready') {
      sendMessage('Привет');
    }
  }, []);

  return (
    <div className="relative flex flex-col h-full bg-canvas">
      {!hasMessages ? (
        <EmptyChat onSend={sendMessage} />
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4 max-w-3xl mx-auto w-full">
          {messages.map((msg, i) => {
            const isLastAgent = msg.role === 'agent' && i === messages.length - 1;
            return (
              <ChatBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
                timestamp={msg.timestamp}
                isStreaming={isLastAgent && isStreaming}
                contentRef={isLastAgent && isStreaming ? streamingRef : undefined}
              />
            );
          })}

          {/* Phase Tracker — visible during streaming OR whenever phases have been activated */}
          {(isStreaming || phases.some(p => p.status !== 'pending')) && (
            <PhaseTracker phases={phases} />
          )}

          {/* Phase 09: Report Preview appears when finish event contains report_url */}
          {reportData && (
            <ReportPreview
              data={reportData}
              onRequestEmail={() => setShowFallback(true)}
            />
          )}

          <div ref={chatEndRef} />
        </div>
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

      {/* Phase 09: Fallback Form modal */}
      {showFallback && (
        <FallbackForm
          sessionId={sessionId}
          reportUrl={reportData?.url}
          onClose={() => setShowFallback(false)}
        />
      )}
    </div>
  );
}

const el = document.getElementById('chat-debug');
if (el) {
  const root = createRoot(el);
  root.render(React.createElement(HermesChat));
}
