/**
 * PromptInput Component
 *
 * Text input with send button for ChatGPT-style interface.
 * Handles Enter key submission and disabled states.
 */

import { useState, type KeyboardEvent } from "react";

export interface PromptInputProps {
  /** Callback when user sends a message */
  onSendMessage: (message: string) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Disabled state */
  disabled?: boolean;
  /** CSS class name */
  className?: string;
}

export function PromptInput({
  onSendMessage,
  placeholder = "Type your message...",
  disabled = false,
  className = "",
}: PromptInputProps) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    const trimmed = input.trim();
    if (trimmed && !disabled) {
      onSendMessage(trimmed);
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`flex items-end gap-2 p-4 border-t border-gray-200 ${className}`}>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        style={{
          minHeight: "44px",
          maxHeight: "200px",
        }}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className="px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        Send
      </button>
    </div>
  );
}

