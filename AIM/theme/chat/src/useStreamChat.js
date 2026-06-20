import { useState, useRef, useCallback, useEffect } from 'react';

const LS_SESSION_KEY = 'aim_session_id';
const LS_MESSAGES_KEY = 'aim_messages';

function loadSessionId() {
  try { return localStorage.getItem(LS_SESSION_KEY); } catch { return null; }
}

function loadMessages() {
  try {
    const raw = localStorage.getItem(LS_MESSAGES_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch { return []; }
}

function saveMessages(msgs) {
  try { localStorage.setItem(LS_MESSAGES_KEY, JSON.stringify(msgs)); } catch {}
}

export function useStreamChat() {
  const [messages, setMessages] = useState(loadMessages);
  const [status, setStatus] = useState('ready');
  const [sessionId, setSessionId] = useState(loadSessionId);
  const abortRef = useRef(null);
  const streamingRef = useRef(null);
  const fullTextRef = useRef('');
  const rafIdRef = useRef(null);
  const assistantIdRef = useRef(null);

  useEffect(() => { saveMessages(messages); }, [messages]);

  useEffect(() => {
    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    };
  }, []);

  const addMessage = useCallback((role, content) => {
    const msg = { id: crypto.randomUUID(), role, content, timestamp: Date.now() };
    setMessages(prev => [...prev, msg]);
    return msg;
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    fullTextRef.current = '';
    setStatus('ready');
  }, []);

  const sendMessage = useCallback(async (text) => {
    if (status === 'streaming' || status === 'submitted') return;
    addMessage('user', text);
    setStatus('submitted');
    fullTextRef.current = '';
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch('/wp-json/aim/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId, mode: 'PRESALE' }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error('HTTP ' + response.status);
      if (!response.body) throw new Error('No response body');

      setStatus('streaming');
      const assistantId = crypto.randomUUID();
      assistantIdRef.current = assistantId;
      setMessages(prev => [...prev, { id: assistantId, role: 'agent', content: '', timestamp: Date.now() }]);

      // RAF loop: write text to DOM + scroll every frame
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
      // Wait for React to commit the empty bubble DOM, then start
      setTimeout(() => {
        rafIdRef.current = requestAnimationFrame(rafLoop);
      }, 0);

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
                if (event.textDelta) {
                  fullTextRef.current += event.textDelta;
                }
                break;
              case 'finish':
                if (event.session_id) {
                  setSessionId(event.session_id);
                  try { localStorage.setItem(LS_SESSION_KEY, event.session_id); } catch {}
                }
                break;
              case 'error':
                // Write error directly to the bubble, then sync to React
                fullTextRef.current = event.message || 'Ошибка';
                if (streamingRef.current) {
                  streamingRef.current.textContent = fullTextRef.current;
                }
                setMessages(prev => {
                  const idx = prev.findIndex(m => m.id === assistantId);
                  if (idx === -1) return prev;
                  const updated = [...prev];
                  updated[idx] = { ...updated[idx], content: fullTextRef.current };
                  return updated;
                });
                setStatus('error');
                break;
              // step-start, step-end, tool-progress — silently ignored
            }
          } catch {
            // skip invalid JSON lines
          }
        }
      }

      // Stop RAF
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }

      // ONE final React sync — triggers persistence + smooth scroll
      const finalText = fullTextRef.current;
      setMessages(prev => {
        const idx = prev.findIndex(m => m.id === assistantId);
        if (idx === -1) return prev;
        const updated = [...prev];
        updated[idx] = { ...updated[idx], content: finalText };
        return updated;
      });

      setStatus('ready');
    } catch (err) {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      if (err.name === 'AbortError') { setStatus('ready'); return; }
      addMessage('agent', 'Извините, произошла ошибка. Попробуйте ещё раз. (' + err.message + ')');
      setStatus('error');
    }
  }, [status, sessionId, addMessage]);

  return { messages, sendMessage, stop, status, sessionId, streamingRef };
}
