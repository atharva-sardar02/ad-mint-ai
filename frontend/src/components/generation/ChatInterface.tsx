/**
 * ChatInterface Component
 *
 * Reusable chat interface for conversational feedback during interactive pipeline.
 * Displays message history and allows users to send feedback messages.
 *
 * Features:
 * - Message list with user/assistant differentiation
 * - Auto-scroll to latest message
 * - Loading indicator for LLM response
 * - Timestamp display
 * - Message input with send button
 */

import React, { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../../types/pipeline";

export interface ChatInterfaceProps {
  /** Chat message history */
  messages: ChatMessage[];
  /** Callback when user sends a message */
  onSendMessage: (message: string) => void;
  /** Whether LLM is currently processing */
  isProcessing?: boolean;
  /** Placeholder text for input */
  placeholder?: string;
  /** Disabled state */
  disabled?: boolean;
  /** CSS class name */
  className?: string;
}

export function ChatInterface({
  messages,
  onSendMessage,
  isProcessing = false,
  placeholder = "Type your feedback here...",
  disabled = false,
  className = "",
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle send message
  const handleSend = () => {
    const trimmed = inputValue.trim();
    if (!trimmed || disabled || isProcessing) return;

    onSendMessage(trimmed);
    setInputValue("");

    // Refocus input
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 rounded-lg">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>No messages yet. Start a conversation!</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.type === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-4 py-2 ${
                  message.type === "user"
                    ? "bg-blue-600 text-white"
                    : message.type === "assistant"
                    ? "bg-white border border-gray-200"
                    : "bg-gray-100 border border-gray-300"
                }`}
              >
                {/* Message Content */}
                <div className="text-sm whitespace-pre-wrap break-words">
                  {message.content}
                </div>

                {/* Timestamp */}
                <div
                  className={`text-xs mt-1 ${
                    message.type === "user"
                      ? "text-blue-200"
                      : "text-gray-500"
                  }`}
                >
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-2">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
                <span className="text-sm text-gray-500">Processing...</span>
              </div>
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Container */}
      <div className="mt-4 flex items-end space-x-2">
        <textarea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isProcessing}
          className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          rows={3}
        />

        <button
          onClick={handleSend}
          disabled={!inputValue.trim() || disabled || isProcessing}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>

      {/* Hint */}
      <div className="mt-2 text-xs text-gray-500 text-center">
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
}
