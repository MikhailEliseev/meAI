'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

type Status = 'ready' | 'submitted' | 'streaming' | 'error';

const SESSION_ID_KEY = 'aim_session_id';
const MESSAGES_KEY = 'aim_messages';

function getSessionId(): string | null {
  try { return localStorage.getItem(SESSION_ID_KEY); } catch { return null; }
}

function getStoredMessages(): Message[] {
  try {
    const stored = localStorage.getItem(MESSAGES_KEY);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((msg) => ({ ...msg, timestamp: new Date(msg.timestamp) }));
  } catch { return []; }
}

function saveMessages(messages: Message[]) {
  try { localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages)); } catch {}
}

export function useChatStream() {
  const [messages, setMessages] = useState<Message[]>(getStoredMessages);
  const [status, setStatus] = useState<Status>('ready');
  const [sessionId, setSessionId] = useState<string | null>(getSessionId);
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingRef = useRef<HTMLDivElement | null>(null);
  const fullTextRef = useRef('');
  const rafIdRef = useRef<number | null>(null);
  const messageIdRef = useRef<string | null>(null);

  useEffect(() => { saveMessages(messages); }, [messages]);

  useEffect(() => {
    return () => {
      if (rafIdRef.current !== null) cancelAnimationFrame(rafIdRef.current);
    };
  }, []);

  const addMessage = useCallback((role: 'user' | 'agent', content: string): Message => {
    const message: Message = { id: crypto.randomUUID(), role, content, timestamp: new Date() };
    setMessages((prev) => [...prev, message]);
    return message;
  }, []);

  const stop = useCallback(() => {
    abortControllerRef.current?.abort();
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    fullTextRef.current = '';
    setStatus('ready');
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (status === 'streaming' || status === 'submitted') return;

    addMessage('user', content);
    setStatus('submitted');
    fullTextRef.current = '';
    if (rafIdRef.current !== null) cancelAnimationFrame(rafIdRef.current);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, session_id: sessionId, mode: 'PRESALE' }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      if (!response.body) throw new Error('No response body');

      setStatus('streaming');

      const messageId = crypto.randomUUID();
      messageIdRef.current = messageId;
      setMessages((prev) => [...prev, { id: messageId, role: 'agent', content: '', timestamp: new Date() }]);

      const rafLoop = () => {
        if (streamingRef.current && fullTextRef.current) {
          streamingRef.current.textContent = fullTextRef.current;
        }
        if (streamingRef.current) {
          const container = streamingRef.current.closest('.overflow-y-auto');
          if (container) container.scrollTop = container.scrollHeight;
        }
        rafIdRef.current = requestAnimationFrame(rafLoop);
      };
      setTimeout(() => { rafIdRef.current = requestAnimationFrame(rafLoop); }, 0);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const data = line.slice(6).trim();
          if (!data) continue;

          try {
            const event = JSON.parse(data);
            switch (event.type) {
              case 'text-delta':
                if (event.textDelta) fullTextRef.current += event.textDelta;
                break;
              case 'finish':
                if (event.session_id) {
                  setSessionId(event.session_id);
                  try { localStorage.setItem(SESSION_ID_KEY, event.session_id); } catch {}
                }
                break;
              case 'error':
                fullTextRef.current = event.message || 'Ошибка';
                if (streamingRef.current) streamingRef.current.textContent = fullTextRef.current;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === messageId ? { ...msg, content: fullTextRef.current } : msg
                  )
                );
                setStatus('error');
                break;
            }
          } catch {}
        }
      }

      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }

      const finalText = fullTextRef.current;
      setMessages((prev) =>
        prev.map((msg) => (msg.id === messageId ? { ...msg, content: finalText } : msg))
      );

      setStatus('ready');
    } catch (error) {
      if (rafIdRef.current !== null) { cancelAnimationFrame(rafIdRef.current); rafIdRef.current = null; }
      if (error instanceof DOMException && error.name === 'AbortError') { setStatus('ready'); return; }
      const errorMessage = error instanceof Error ? error.message : String(error);
      addMessage('agent', `Извините, произошла ошибка. Попробуйте ещё раз. (${errorMessage})`);
      setStatus('error');
    }
  }, [status, sessionId, addMessage]);

  const reset = useCallback(() => {
    stop();
    setMessages([]);
    setSessionId(null);
    fullTextRef.current = '';
    messageIdRef.current = null;
    try {
      localStorage.removeItem(SESSION_ID_KEY);
      localStorage.removeItem(MESSAGES_KEY);
    } catch {}
  }, [stop]);

  return { messages, sendMessage, stop, reset, status, sessionId, streamingRef };
}
