/**
 * ChatFeed Component
 *
 * Scrollable message history display for ChatGPT-style interface.
 * Displays conversation messages with auto-scroll to latest.
 */

import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../types/pipeline";
import { MessageBubble } from "./MessageBubble";

export interface ChatFeedProps {
  /** Chat message history */
  messages: ChatMessage[];
  /** CSS class name */
  className?: string;
}

/**
 * Format timestamp for display
 */
function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function ChatFeed({ messages, className = "" }: ChatFeedProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className={`flex-1 overflow-y-auto p-4 space-y-4 ${className}`}>
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <p>No messages yet. Start a conversation!</p>
        </div>
      ) : (
        <>
          {messages.map((message, index) => (
            <MessageBubble
              key={index}
              message={message}
              timestamp={formatTime(message.timestamp)}
            />
          ))}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
}

