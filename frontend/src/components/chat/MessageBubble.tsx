/**
 * MessageBubble Component
 *
 * Displays individual chat messages (user, assistant, system).
 * Styled with ChatGPT-like appearance.
 */

import React from "react";
import type { ChatMessage } from "../../types/pipeline";

export interface MessageBubbleProps {
  /** Chat message to display */
  message: ChatMessage;
  /** Formatted timestamp string */
  timestamp: string;
}

export function MessageBubble({ message, timestamp }: MessageBubbleProps) {
  const isUser = message.type === "user";
  const isSystem = message.type === "system";

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`max-w-[70%] rounded-lg px-4 py-2 ${
          isUser
            ? "bg-blue-600 text-white"
            : isSystem
            ? "bg-gray-100 border border-gray-300 text-gray-700"
            : "bg-white border border-gray-200 text-gray-900"
        }`}
      >
        {/* Message Content */}
        <div className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </div>

        {/* Timestamp */}
        <div
          className={`text-xs mt-1 ${
            isUser
              ? "text-blue-200"
              : isSystem
              ? "text-gray-500"
              : "text-gray-500"
          }`}
        >
          {timestamp}
        </div>

        {/* Metadata (optional) */}
        {message.metadata && Object.keys(message.metadata).length > 0 && (
          <div className="mt-2 text-xs opacity-75">
            {message.metadata.quality_score !== undefined && (
              <span>Quality: {message.metadata.quality_score}/100</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

