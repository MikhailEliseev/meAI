'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

interface Progress {
  step: string;
  stepIndex: number;
  totalSteps: number;
  liveMessage?: string;
}

type Status = 'ready' | 'submitted' | 'streaming' | 'error';

const SESSION_ID_KEY = 'aim_session_id_old';
const MESSAGES_KEY = 'aim_messages_old';

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

export function useChatStreamOld() {
  const [messages, setMessages] = useState<Message[]>(getStoredMessages);
  const [status, setStatus] = useState<Status>('ready');
  const [sessionId, setSessionId] = useState<string | null>(getSessionId);
  const [progress, setProgress] = useState<Progress | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messageIdRef = useRef<string | null>(null);

  useEffect(() => { saveMessages(messages); }, [messages]);

  const addMessage = useCallback((role: 'user' | 'agent', content: string): Message => {
    const message: Message = { id: crypto.randomUUID(), role, content, timestamp: new Date() };
    setMessages((prev) => [...prev, message]);
    return message;
  }, []);

  const stop = useCallback(() => {
    abortControllerRef.current?.abort();
    setProgress(null);
    setStatus('ready');
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (status === 'streaming' || status === 'submitted') return;

    addMessage('user', content);
    setStatus('submitted');
    setProgress(null);

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
      let fullText = '';

      setMessages((prev) => [...prev, { id: messageId, role: 'agent', content: '', timestamp: new Date() }]);

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
              case 'step-start':
                setProgress({
                  step: event.step || '',
                  stepIndex: event.stepIndex || 0,
                  totalSteps: event.totalSteps || 1,
                });
                break;
              case 'step-end':
                if (event.liveMessage) {
                  setProgress((prev) => prev ? { ...prev, liveMessage: event.liveMessage } : null);
                }
                break;
              case 'tool-progress':
                setProgress((prev) =>
                  prev ? { ...prev, liveMessage: event.message || prev.liveMessage } : null
                );
                break;
              case 'text-delta':
                if (event.textDelta) {
                  fullText += event.textDelta;
                  // React state update on EVERY text-delta — causes flickering
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === messageId ? { ...msg, content: fullText } : msg
                    )
                  );
                }
                break;
              case 'finish':
                if (event.session_id) {
                  setSessionId(event.session_id);
                  try { localStorage.setItem(SESSION_ID_KEY, event.session_id); } catch {}
                }
                break;
              case 'error':
                fullText = event.message || 'Ошибка';
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === messageId ? { ...msg, content: fullText } : msg
                  )
                );
                setStatus('error');
                break;
            }
          } catch {}
        }
      }

      setMessages((prev) =>
        prev.map((msg) => (msg.id === messageId ? { ...msg, content: fullText } : msg))
      );

      setProgress(null);
      setStatus('ready');
    } catch (error) {
      setProgress(null);
      if (error instanceof DOMException && error.name === 'AbortError') { setStatus('ready'); return; }
      const errorMessage = error instanceof Error ? error.message : String(error);
      addMessage('agent', `Извините, произошла ошибка. Попробуйте ещё раз. (${errorMessage})`);
      setStatus('error');
    }
  }, [status, sessionId, addMessage]);

  return { messages, sendMessage, stop, status, sessionId, progress };
}
