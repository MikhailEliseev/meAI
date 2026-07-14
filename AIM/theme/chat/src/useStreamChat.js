import { useState, useRef, useCallback, useEffect } from 'react';
import { PHASES, PHASE_DURATIONS, calculateETA } from './components/PhaseTracker';

const LS_SESSION_KEY = 'aim_session_id';
const LS_MESSAGES_KEY = 'aim_messages';
const LS_PIPELINE_START_KEY = 'aim_pipeline_start';

// Watchdog: если нет SSE событий дольше этого — показать предупреждение
const WATCHDOG_WARN_MS = 90_000;   // 90 сек
const WATCHDOG_TIMEOUT_MS = 180_000; // 180 сек

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
  const [etaSeconds, setEtaSeconds] = useState(0);
  const [connectionWarning, setConnectionWarning] = useState(null);

  const abortRef = useRef(null);
  const streamingRef = useRef(null);
  const fullTextRef = useRef('');
  const rafIdRef = useRef(null);
  const assistantIdRef = useRef(null);

  // ETA tracking refs
  const phaseStartTimeRef = useRef(null);
  const etaIntervalRef = useRef(null);

  // Watchdog refs
  const lastEventTimeRef = useRef(Date.now());
  const watchdogIntervalRef = useRef(null);

  useEffect(() => { saveMessages(messages); }, [messages]);

  // Cleanup all intervals on unmount
  useEffect(() => {
    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      if (etaIntervalRef.current) clearInterval(etaIntervalRef.current);
      if (watchdogIntervalRef.current) clearInterval(watchdogIntervalRef.current);
    };
  }, []);

  const addMessage = useCallback((role, content) => {
    const msg = { id: crypto.randomUUID(), role, content, timestamp: Date.now() };
    setMessages(prev => [...prev, msg]);
    return msg;
  }, []);

  // ─── ETA Timer ───
  const startETATimer = useCallback(() => {
    if (etaIntervalRef.current) clearInterval(etaIntervalRef.current);
    setEtaSeconds(14 * 60); // начинаем с ~14 мин

    etaIntervalRef.current = setInterval(() => {
      const workingPhase = phasesRef.current.find(p => p.status === 'working');
      if (!workingPhase) return;

      const elapsed = phaseStartTimeRef.current
        ? Math.floor((Date.now() - phaseStartTimeRef.current) / 1000)
        : 0;

      const eta = calculateETA(workingPhase.id, elapsed);
      setEtaSeconds(eta);
    }, 1000);
  }, []);

  const stopETATimer = useCallback(() => {
    if (etaIntervalRef.current) {
      clearInterval(etaIntervalRef.current);
      etaIntervalRef.current = null;
    }
  }, []);

  // ─── Watchdog ───
  const startWatchdog = useCallback(() => {
    if (watchdogIntervalRef.current) clearInterval(watchdogIntervalRef.current);
    lastEventTimeRef.current = Date.now();

    watchdogIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - lastEventTimeRef.current;
      if (elapsed > WATCHDOG_TIMEOUT_MS) {
        // Timeout — даём пользователю понятное сообщение и останавливаем
        stopETATimer();
        setConnectionWarning(null);
        addMessage('agent', '⏳ Анализ занимает дольше обычного, но продолжается в фоновом режиме. Ваш отчёт будет готов через несколько минут — ссылка появится здесь автоматически.');
        setStatus('ready');
        if (abortRef.current) abortRef.current.abort();
        if (watchdogIntervalRef.current) clearInterval(watchdogIntervalRef.current);
      } else if (elapsed > WATCHDOG_WARN_MS) {
        setConnectionWarning('⚠️ Долго нет ответа от сервера…');
      } else {
        setConnectionWarning(null);
      }
    }, 15_000); // проверяем каждые 15 сек
  }, [addMessage, stopETATimer]);

  const stopWatchdog = useCallback(() => {
    if (watchdogIntervalRef.current) {
      clearInterval(watchdogIntervalRef.current);
      watchdogIntervalRef.current = null;
    }
    setConnectionWarning(null);
  }, []);

  // Ref чтобы читать phases внутри interval без stale closure
  const phasesRef = useRef(phases);
  useEffect(() => { phasesRef.current = phases; }, [phases]);

  const updatePhase = useCallback((stage, message) => {
    const phase = PHASES.find(p => p.stages.includes(stage));
    if (!phase) return;

    lastEventTimeRef.current = Date.now();

    setPhases(prev => prev.map(p => {
      if (p.id !== phase.id) return p;
      // Не понижаем завершённую фазу обратно в working
      // (более поздние фазы тоже вызывают perplexity_search и т.д.)
      if (p.status === 'done') return p;

      // Сбрасываем время начала фазы при переходе
      if (p.status !== 'working') {
        phaseStartTimeRef.current = Date.now();
      }

      const counterMatch = message?.match(/(\d+)\s+(конкурент|врач|отзыв|упоминани|страниц|стат|доктор|клиник)/i);
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
    stopETATimer();
    stopWatchdog();
    setStatus('ready');
  }, [stopETATimer, stopWatchdog]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setPhases(PHASES.map(p => ({ ...p, status: 'pending', counter: null })));
    setReportData(null);
    setSessionId(null);
    setEtaSeconds(0);
    setConnectionWarning(null);
    fullTextRef.current = '';
    phaseStartTimeRef.current = null;
    stopETATimer();
    stopWatchdog();
    try { localStorage.removeItem(LS_MESSAGES_KEY); } catch {}
    try { localStorage.removeItem(LS_SESSION_KEY); } catch {}
    try { localStorage.removeItem(LS_PIPELINE_START_KEY); } catch {}
  }, [stopETATimer, stopWatchdog]);

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
      setTimeout(() => {
        rafIdRef.current = requestAnimationFrame(rafLoop);
      }, 0);

      // Стартуем ETA таймер и watchdog
      startETATimer();
      startWatchdog();
      lastEventTimeRef.current = Date.now();

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE events separated by \n\n (proper frame boundary)
        const frames = buffer.split('\n\n');
        buffer = frames.pop() || '';

        for (const frame of frames) {
          // Each frame may have multiple data: lines
          const lines = frame.split('\n');
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const data = line.slice(6).trim();
            if (!data) continue;
            try {
              const event = JSON.parse(data);
              lastEventTimeRef.current = Date.now(); // any event = alive

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
                    // Сбрасываем время фазы при started
                    if (event.status === 'started') {
                      phaseStartTimeRef.current = Date.now();
                    }
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
                  // При finish ВСЕГДА сбрасываем все фазы в done
                  // (pipeline завершён, даже если report_url не передан)
                  setPhases(prev => prev.map(p => ({ ...p, status: 'done' })));
                  if (event.report_url) {
                    setReportData({
                      url: event.report_url,
                      title: event.report_title || 'Разведка пресейла',
                      stats: [],
                    });
                  }
                  stopETATimer();
                  stopWatchdog();
                  break;

                case 'suggestions':
                  // Кнопки от модели — сохраняем в текущее сообщение ассистента
                  if (event.buttons && event.buttons.length) {
                    setMessages(prev => {
                      const idx = prev.findIndex(m => m.id === assistantId);
                      if (idx === -1) return prev;
                      const updated = [...prev];
                      updated[idx] = { ...updated[idx], buttons: event.buttons };
                      return updated;
                    });
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
                  stopETATimer();
                  stopWatchdog();
                  break;

                case 'error':
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
                  stopETATimer();
                  stopWatchdog();
                  break;
              }
            } catch {
              // skip invalid JSON lines
            }
          }
        }
      }

      // Stop RAF
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }

      // Final React sync
      const finalText = fullTextRef.current;
      setMessages(prev => {
        const idx = prev.findIndex(m => m.id === assistantId);
        if (idx === -1) return prev;
        const updated = [...prev];
        updated[idx] = { ...updated[idx], content: finalText };
        return updated;
      });

      stopETATimer();
      stopWatchdog();
      setStatus('ready');
    } catch (err) {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      stopETATimer();
      stopWatchdog();
      if (err.name === 'AbortError') { setStatus('ready'); return; }
      addMessage('agent', 'Извините, произошла ошибка. Попробуйте ещё раз. (' + err.message + ')');
      setStatus('error');
    }
  }, [status, sessionId, addMessage, updatePhase, startETATimer, stopETATimer, startWatchdog, stopWatchdog]);

  return { messages, sendMessage, clearMessages, stop, status, sessionId, streamingRef, phases, reportData, etaSeconds, connectionWarning };
}
