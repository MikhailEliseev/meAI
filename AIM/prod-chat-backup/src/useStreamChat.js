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
  const [progress, setProgress] = useState(null);
  const [sessionId, setSessionId] = useState(loadSessionId);
  const abortRef = useRef(null);
  const toolStepsRef = useRef([]);

  useEffect(() => { saveMessages(messages); }, [messages]);

  const addMessage = useCallback((role, content) => {
    const msg = { id: crypto.randomUUID(), role, content, timestamp: Date.now() };
    setMessages(prev => [...prev, msg]);
    return msg;
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setStatus('ready');
    setProgress(null);
  }, []);

  const sendMessage = useCallback(async (text) => {
    if (status === 'streaming' || status === 'submitted') return;
    addMessage('user', text);
    setStatus('submitted');
    setProgress(null);
    toolStepsRef.current = [];

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
      setMessages(prev => [...prev, { id: assistantId, role: 'agent', content: '', timestamp: Date.now() }]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // Parse JSON-lines: one JSON object per line
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);
            switch (event.type) {
              case 'step-start':
                if (event.step) {
                  toolStepsRef.current.push(event.step);
                  setProgress({
                    step: event.step,
                    stepIndex: toolStepsRef.current.length - 1,
                    totalSteps: toolStepsRef.current.length,
                  });
                }
                break;
              case 'step-end':
                setProgress(prev => prev ? { ...prev, liveMessage: undefined } : null);
                break;
              case 'tool-progress':
                setProgress(prev => ({
                  step: prev?.step || event.stage || 'analysing',
                  stepIndex: prev?.stepIndex ?? 0,
                  totalSteps: prev?.totalSteps ?? 1,
                  liveMessage: event.message,
                }));
                break;
              case 'text-delta':
                if (event.textDelta) {
                  setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: m.content + event.textDelta } : m));
                }
                break;
              case 'suggestions':
                if (event.buttons && event.buttons.length) {
                  setMessages(prev => prev.map(m =>
                    m.id === assistantId ? { ...m, buttons: event.buttons } : m
                  ));
                }
                break;
              case 'finish':
                if (event.session_id) {
                  setSessionId(event.session_id);
                  try { localStorage.setItem(LS_SESSION_KEY, event.session_id); } catch {}
                }
                break;
              case 'error':
                setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: m.content || event.message || 'Ошибка' } : m));
                setStatus('error');
                break;
            }
          } catch {
            // skip invalid JSON lines
          }
        }
      }
      setStatus('ready');
      setProgress(null);
    } catch (err) {
      if (err.name === 'AbortError') { setStatus('ready'); setProgress(null); return; }
      addMessage('agent', 'Извините, произошла ошибка. Попробуйте ещё раз. (' + err.message + ')');
      setStatus('error');
      setProgress(null);
    }
  }, [status, sessionId, addMessage]);

  return { messages, sendMessage, stop, status, progress, sessionId };
}
