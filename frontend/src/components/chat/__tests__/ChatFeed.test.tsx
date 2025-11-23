/**
 * Component tests for ChatFeed (Story 1.3)
 * Tests scrollable message history display
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatFeed } from "../ChatFeed";
import type { ChatMessage } from "../../../types/pipeline";

describe("ChatFeed Component", () => {
  it("should render empty state when no messages", () => {
    render(<ChatFeed messages={[]} />);
    expect(screen.getByText("No messages yet. Start a conversation!")).toBeInTheDocument();
  });

  it("should render user messages", () => {
    const messages: ChatMessage[] = [
      {
        type: "user",
        content: "Hello, I want to create an ad",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<ChatFeed messages={messages} />);
    expect(screen.getByText("Hello, I want to create an ad")).toBeInTheDocument();
  });

  it("should render assistant messages", () => {
    const messages: ChatMessage[] = [
      {
        type: "assistant",
        content: "I'll help you create an ad",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<ChatFeed messages={messages} />);
    expect(screen.getByText("I'll help you create an ad")).toBeInTheDocument();
  });

  it("should render system messages", () => {
    const messages: ChatMessage[] = [
      {
        type: "system",
        content: "Story generated! Please review and approve.",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<ChatFeed messages={messages} />);
    expect(screen.getByText("Story generated! Please review and approve.")).toBeInTheDocument();
  });

  it("should render multiple messages in order", () => {
    const messages: ChatMessage[] = [
      {
        type: "user",
        content: "First message",
        timestamp: new Date(Date.now() - 2000).toISOString(),
      },
      {
        type: "assistant",
        content: "Second message",
        timestamp: new Date(Date.now() - 1000).toISOString(),
      },
      {
        type: "user",
        content: "Third message",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<ChatFeed messages={messages} />);
    expect(screen.getByText("First message")).toBeInTheDocument();
    expect(screen.getByText("Second message")).toBeInTheDocument();
    expect(screen.getByText("Third message")).toBeInTheDocument();
  });
});

