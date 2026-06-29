import { useState, useRef, useCallback, useEffect } from 'react';
import { PHASES } from './components/PhaseTracker';

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
  const [phases, setPhases] = useState(() => PHASES.map(p => ({ ...p, status: 'pending', counter: null })));
  const [reportData, setReportData] = useState(null);
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

  const updatePhase = useCallback((stage, message) => {
    const phase = PHASES.find(p => p.stages.includes(stage));
    if (!phase) return;

    setPhases(prev => prev.map(p => {
      if (p.id !== phase.id) return p;

      // Extract counter from message: "Найдено 5 конкурентов" → "5 конкурентов"
      const counterMatch = message.match(/(\d+)\s+(конкурент|врач|отзыв|упоминани|страниц|стат|доктор|клиник)/i);
      const counter = counterMatch ? `${counterMatch[1]} ${counterMatch[2]}` : null;

      return { ...p, status: 'working', counter };
    }));
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

  const clearMessages = useCallback(() => {
    setMessages([]);
    setPhases(PHASES.map(p => ({ ...p, status: 'pending', counter: null })));
    setReportData(null);
    setSessionId(null);
    fullTextRef.current = '';
    try { localStorage.removeItem(LS_MESSAGES_KEY); } catch {}
    try { localStorage.removeItem(LS_SESSION_KEY); } catch {}
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
      const response = await fetch('/api/chat/stream', {
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
              case 'tool-progress':
                if (event.stage && event.message) {
                  updatePhase(event.stage, event.message);
                }
                break;
              case 'phase-progress':
                if (event.phase_id !== undefined && event.status) {
                  setPhases(prev => prev.map(p => {
                    if (p.id !== event.phase_id) return p;
                    const newStatus = event.status === 'started' ? 'working'
                      : (event.status === 'completed' || event.status === 'no_data') ? 'done'
                      : 'pending';
                    return {
                      ...p,
                      status: newStatus,
                      counter: event.message || p.counter,
                    };
                  }));
                }
                break;
              case 'finish':
                if (event.session_id) {
                  setSessionId(event.session_id);
                  try { localStorage.setItem(LS_SESSION_KEY, event.session_id); } catch {}
                }
                // Phase 09: Extract report data
                if (event.report_url) {
                  setReportData({
                    url: event.report_url,
                    title: event.report_title || 'Разведка пресейла',
                    stats: event.session_hash ? [] : [],
                  });
                  setPhases(prev => prev.map(p => ({ ...p, status: 'done' })));
                }
                break;
              case 'report-ready':
                if (event.url) {
                  setReportData({
                    url: event.url,
                    title: event.title || 'Разведка пресейла',
                    stats: [],
                  });
                  setPhases(prev => prev.map(p => ({ ...p, status: 'done' })));
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
  }, [status, sessionId, addMessage, updatePhase]);

  return { messages, sendMessage, clearMessages, stop, status, sessionId, streamingRef, phases, reportData };
}
