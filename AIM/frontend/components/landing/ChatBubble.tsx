"use client";

import React from "react";
import { motion } from "framer-motion";
import { Streamdown } from "streamdown";
import { cn } from "@/lib/utils";

interface ChatBubbleProps {
  role: "agent" | "user";
  content: string;
  timestamp?: Date;
  isStreaming?: boolean;
}

export function ChatBubble({ role, content, timestamp, isStreaming }: ChatBubbleProps) {
  const isAgent = role === "agent";
  const isEmpty = !content.trim();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn("flex gap-3 max-w-[85%]", isAgent ? "self-start" : "self-end flex-row-reverse")}
    >
      {/* Avatar */}
      <div
        className={cn(
          "w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-bold",
          isAgent
            ? "bg-gradient-to-br from-primary-500 to-primary-700 text-white"
            : "bg-gray-200 text-gray-600"
        )}
      >
        {isAgent ? "AI" : "Вы"}
      </div>

      {/* Bubble */}
      <div
        className={cn(
          "rounded-2xl px-4 py-3 text-sm leading-relaxed min-w-0 overflow-hidden",
          isAgent
            ? "bg-white border border-gray-100 text-gray-800 shadow-sm"
            : "bg-primary-600 text-white"
        )}
      >
        {isAgent ? (
          <div className="prose prose-sm prose-stone max-w-none [&_table]:text-xs [&_th]:text-xs [&_td]:text-xs [&_pre]:text-xs">
            <Streamdown remend={isStreaming ? {} : undefined}>{content}</Streamdown>
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{content}</p>
        )}
        {isStreaming && isEmpty && (
          <span className="inline-flex gap-1">
            <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
          </span>
        )}
        {timestamp && (
          <span className="block text-xs mt-1 opacity-50">
            {timestamp.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}
          </span>
        )}
      </div>
    </motion.div>
  );
}
