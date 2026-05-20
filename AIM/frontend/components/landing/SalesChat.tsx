"use client";

import React, { useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { EmptyChat } from "./EmptyChat";
import { ProgressSteps } from "./ProgressSteps";
import { useStreamChat } from "@/hooks/useStreamChat";
import { cn } from "@/lib/utils";

export function SalesChat({ className }: { className?: string }) {
  const { messages, sendMessage, stop, status, progress } = useStreamChat();
  const chatEndRef = useRef<HTMLDivElement>(null);
  const isStreaming = status === "streaming" || status === "submitted";
  const hasMessages = messages.length > 0;

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, progress, scrollToBottom]);

  return (
    <section
      className={cn(
        "relative flex flex-col h-screen",
        "bg-canvas",
        className,
      )}
      aria-labelledby="chat-heading"
    >
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-border-hairline bg-canvas/80 backdrop-blur sticky top-0 z-10 h-14 shrink-0">
        <a href="/" className="flex items-center gap-2 font-bold text-lg text-ink no-underline">
          <span className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
            <span className="text-white font-bold text-xs">AI</span>
          </span>
          AIM
        </a>
        <a
          href="/about"
          className="text-sm text-text-muted hover:text-ink transition-colors"
        >
          О компании
        </a>
      </header>

      {/* Chat area */}
      {!hasMessages ? (
        <EmptyChat onSend={sendMessage} />
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4 max-w-3xl mx-auto w-full">
          <AnimatePresence>
            {messages.map((msg, i) => {
              const isLastAgent =
                msg.role === "agent" && i === messages.length - 1;
              return (
                <ChatBubble
                  key={msg.id}
                  role={msg.role}
                  content={msg.content}
                  timestamp={msg.timestamp}
                  isStreaming={isLastAgent && isStreaming}
                />
              );
            })}
          </AnimatePresence>

          {/* Progress steps during tool calls */}
          {progress && <ProgressSteps progress={progress} />}

          <div ref={chatEndRef} />
        </div>
      )}

      {/* Sticky bottom input */}
      {hasMessages && (
        <div className="sticky bottom-0 bg-canvas border-t border-border-hairline max-w-3xl mx-auto w-full">
          <ChatInput
            onSend={sendMessage}
            onStop={stop}
            isStreaming={isStreaming}
            disabled={!isStreaming && status === "error"}
          />
        </div>
      )}
    </section>
  );
}
