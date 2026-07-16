import { useState, useRef, useCallback, useEffect } from 'react';
import { PHASES } from './components/PhaseTracker';

const LS_SESSION_KEY = 'aim_session_id';
const LS_MESSAGES_KEY = 'aim_messages';

// Mock data for debugging UI
const MOCK_RESPONSE = `Анализирую ваш сайт и конкурентов...

**Найдено 5 основных конкурентов:**
- Клиника А (позиция #2 в Яндекс)
- Клиника Б (позиция #3 в Яндекс)
- Клиника В (позиция #5 в Google)

**Проблемы на вашем сайте:**
1. Медленная загрузка страницы (3.2 сек)
2. Отсутствие мобильной версии
3. Устаревший дизайн

**Рекомендации:**
- Оптимизировать изображения
- Внедрить адаптивный дизайн
- Обновить контент страницы`;

const MOCK_PHASES = [
  { stage: 'analyze_site', message: 'Анализирую структуру сайта...', delay: 500 },
  { stage: 'fetch_competitors', message: 'Собираю данные конкурентов...', delay: 1500 },
  { stage: 'analyze_competitors', message: 'Анализирую конкурентов...', delay: 3000 },
  { stage: 'generate_insights', message: 'Формирую рекомендации...', delay: 4500 },
];

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
    setPhases(prev => prev.map(p =>
      p.id === phase.id ? { ...p, status: 'active', counter: message } : p
    ));
  }, []);

  const completePhase = useCallback((stage) => {
    const phase = PHASES.find(p => p.stages.includes(stage));
    if (!phase) return;
    setPhases(prev => prev.map(p =>
      p.id === phase.id ? { ...p, status: 'complete', counter: null } : p
    ));
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setPhases(PHASES.map(p => ({ ...p, status: 'pending', counter: null })));
    setReportData(null);
    setStatus('ready');
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

    // Mock streaming simulation
    const mockSession = sessionId || crypto.randomUUID();
    if (!sessionId) {
      setSessionId(mockSession);
      try { localStorage.setItem(LS_SESSION_KEY, mockSession); } catch {}
    }

    setStatus('streaming');
    const assistantId = crypto.randomUUID();
    assistantIdRef.current = assistantId;
    setMessages(prev => [...prev, { id: assistantId, role: 'agent', content: '', timestamp: Date.now() }]);

    // RAF loop for smooth text updates
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

    // Simulate phase updates
    MOCK_PHASES.forEach(({ stage, message, delay }) => {
      setTimeout(() => {
        updatePhase(stage, message);
        setTimeout(() => completePhase(stage), 800);
      }, delay);
    });

    // Simulate streaming text
    const words = MOCK_RESPONSE.split(' ');
    for (let i = 0; i < words.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 50 + Math.random() * 50));
      fullTextRef.current += (i > 0 ? ' ' : '') + words[i];
    }

    // Finalize
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    rafIdRef.current = null;

    setMessages(prev => prev.map(m =>
      m.id === assistantId ? { ...m, content: fullTextRef.current } : m
    ));

    // Mock report data
    setTimeout(() => {
      setReportData({
        url: 'https://iamaim.ru/reports/mock-report.pdf',
        title: 'Отчёт по анализу конкурентов',
        pages: 12,
        size: '2.4 MB'
      });
    }, 1000);

    setStatus('ready');
  }, [status, sessionId, addMessage, updatePhase, completePhase]);

  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    if (assistantIdRef.current && fullTextRef.current) {
      setMessages(prev => prev.map(m =>
        m.id === assistantIdRef.current ? { ...m, content: fullTextRef.current } : m
      ));
    }
    setStatus('ready');
  }, []);

  return {
    messages,
    sendMessage,
    clearMessages,
    stop,
    status,
    streamingRef,
    phases,
    reportData,
    sessionId,
  };
}
