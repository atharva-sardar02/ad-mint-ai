/**
 * Component tests for MessageBubble (Story 1.3)
 * Tests individual message display
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageBubble } from "../MessageBubble";
import type { ChatMessage } from "../../../types/pipeline";

describe("MessageBubble Component", () => {
  it("should render user message with blue background", () => {
    const message: ChatMessage = {
      type: "user",
      content: "User message",
      timestamp: new Date().toISOString(),
    };

    render(<MessageBubble message={message} timestamp="Just now" />);
    const bubble = screen.getByText("User message").closest("div");
    expect(bubble).toHaveClass("bg-blue-600");
  });

  it("should render assistant message with white background", () => {
    const message: ChatMessage = {
      type: "assistant",
      content: "Assistant message",
      timestamp: new Date().toISOString(),
    };

    render(<MessageBubble message={message} timestamp="Just now" />);
    const bubble = screen.getByText("Assistant message").closest("div");
    expect(bubble).toHaveClass("bg-white");
  });

  it("should render system message with gray background", () => {
    const message: ChatMessage = {
      type: "system",
      content: "System message",
      timestamp: new Date().toISOString(),
    };

    render(<MessageBubble message={message} timestamp="Just now" />);
    const bubble = screen.getByText("System message").closest("div");
    expect(bubble).toHaveClass("bg-gray-100");
  });

  it("should display timestamp", () => {
    const message: ChatMessage = {
      type: "user",
      content: "Test message",
      timestamp: new Date().toISOString(),
    };

    render(<MessageBubble message={message} timestamp="2m ago" />);
    expect(screen.getByText("2m ago")).toBeInTheDocument();
  });

  it("should display quality score metadata if present", () => {
    const message: ChatMessage = {
      type: "system",
      content: "Story generated",
      timestamp: new Date().toISOString(),
      metadata: {
        quality_score: 85,
      },
    };

    render(<MessageBubble message={message} timestamp="Just now" />);
    expect(screen.getByText(/Quality: 85\/100/)).toBeInTheDocument();
  });
});

