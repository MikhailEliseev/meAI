"use client";

import { useState, useRef, useCallback, useEffect } from "react";

const LS_SESSION_KEY = "aim_session_id";
const LS_MESSAGES_KEY = "aim_messages";

function loadSessionId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(LS_SESSION_KEY);
  } catch {
    return null;
  }
}

function loadMessages(): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(LS_MESSAGES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((m: Message) => ({ ...m, timestamp: new Date(m.timestamp) }));
  } catch {
    return [];
  }
}

function saveMessages(msgs: Message[]) {
  try {
    localStorage.setItem(LS_MESSAGES_KEY, JSON.stringify(msgs));
  } catch { /* quota exceeded — ignore */ }
}

export interface Message {
  id: string;
  role: "agent" | "user";
  content: string;
  timestamp: Date;
}

export interface StreamProgress {
  step: string;
  stepIndex: number;
  totalSteps: number;
}

export type StreamStatus = "ready" | "submitted" | "streaming" | "error";

interface SSEEvent {
  type: "step-start" | "step-end" | "text-delta" | "finish" | "error";
  step?: string;
  textDelta?: string;
  session_id?: string;
  message?: string;
}

export function useStreamChat() {
  const [messages, setMessages] = useState<Message[]>(loadMessages);
  const [status, setStatus] = useState<StreamStatus>("ready");
  const [progress, setProgress] = useState<StreamProgress | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(loadSessionId);
  const abortRef = useRef<AbortController | null>(null);
  const toolStepsRef = useRef<string[]>([]);

  // Persist messages to localStorage on every change
  useEffect(() => {
    saveMessages(messages);
  }, [messages]);

  const addMessage = useCallback((role: "agent" | "user", content: string) => {
    const msg: Message = {
      id: crypto.randomUUID(),
      role,
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, msg]);
    return msg;
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setStatus("ready");
    setProgress(null);
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (status === "streaming" || status === "submitted") return;

      addMessage("user", text);
      setStatus("submitted");
      setProgress(null);
      toolStepsRef.current = [];

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await fetch("/api/chat/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            session_id: sessionId,
            mode: "PRESALE",
          }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        setStatus("streaming");

        // Add empty assistant message to fill with deltas
        const assistantId = crypto.randomUUID();
        setMessages((prev) => [
          ...prev,
          {
            id: assistantId,
            role: "agent",
            content: "",
            timestamp: new Date(),
          },
        ]);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Parse SSE frames: "data: {...}\n\n"
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // keep incomplete line in buffer

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const event: SSEEvent = JSON.parse(jsonStr);

              switch (event.type) {
                case "step-start":
                  if (event.step) {
                    toolStepsRef.current.push(event.step);
                    setProgress({
                      step: event.step,
                      stepIndex: toolStepsRef.current.length - 1,
                      totalSteps: toolStepsRef.current.length,
                    });
                  }
                  break;

                case "step-end":
                  // step completed, keep progress visible
                  break;

                case "text-delta":
                  if (event.textDelta) {
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantId
                          ? { ...m, content: m.content + event.textDelta }
                          : m,
                      ),
                    );
                  }
                  break;

                case "finish":
                  if (event.session_id) {
                    setSessionId(event.session_id);
                    try {
                      localStorage.setItem(LS_SESSION_KEY, event.session_id);
                    } catch { /* ignore */ }
                  }
                  break;

                case "error":
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, content: m.content || event.message || "Ошибка" }
                        : m,
                    ),
                  );
                  setStatus("error");
                  break;
              }
            } catch {
              // skip invalid JSON frames
            }
          }
        }

        setStatus("ready");
        setProgress(null);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
          // user stopped — assistant message already rendered with partial content
          setStatus("ready");
          setProgress(null);
          return;
        }
        const message = err instanceof Error ? err.message : String(err);
        addMessage(
          "agent",
          `Извините, произошла ошибка. Попробуйте ещё раз. (${message})`,
        );
        setStatus("error");
        setProgress(null);
      }
    },
    [status, sessionId, addMessage],
  );

  return { messages, sendMessage, stop, status, progress, sessionId };
}
