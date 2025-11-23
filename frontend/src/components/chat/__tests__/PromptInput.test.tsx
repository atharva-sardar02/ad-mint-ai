/**
 * Component tests for PromptInput (Story 1.3)
 * Tests text input with send button
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PromptInput } from "../PromptInput";

describe("PromptInput Component", () => {
  it("should render input and send button", () => {
    const onSendMessage = vi.fn();
    render(<PromptInput onSendMessage={onSendMessage} />);

    expect(screen.getByPlaceholderText("Type your message...")).toBeInTheDocument();
    expect(screen.getByText("Send")).toBeInTheDocument();
  });

  it("should call onSendMessage when send button clicked", async () => {
    const user = userEvent.setup();
    const onSendMessage = vi.fn();
    render(<PromptInput onSendMessage={onSendMessage} />);

    const input = screen.getByPlaceholderText("Type your message...");
    const sendButton = screen.getByText("Send");

    await user.type(input, "Test message");
    await user.click(sendButton);

    expect(onSendMessage).toHaveBeenCalledWith("Test message");
  });

  it("should call onSendMessage when Enter key pressed", async () => {
    const user = userEvent.setup();
    const onSendMessage = vi.fn();
    render(<PromptInput onSendMessage={onSendMessage} />);

    const input = screen.getByPlaceholderText("Type your message...");
    await user.type(input, "Test message{Enter}");

    expect(onSendMessage).toHaveBeenCalledWith("Test message");
  });

  it("should not send empty message", async () => {
    const user = userEvent.setup();
    const onSendMessage = vi.fn();
    render(<PromptInput onSendMessage={onSendMessage} />);

    const sendButton = screen.getByText("Send");
    expect(sendButton).toBeDisabled();

    await user.click(sendButton);
    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it("should be disabled when disabled prop is true", () => {
    const onSendMessage = vi.fn();
    render(<PromptInput onSendMessage={onSendMessage} disabled={true} />);

    const input = screen.getByPlaceholderText("Type your message...");
    const sendButton = screen.getByText("Send");

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it("should clear input after sending", async () => {
    const user = userEvent.setup();
    const onSendMessage = vi.fn();
    render(<PromptInput onSendMessage={onSendMessage} />);

    const input = screen.getByPlaceholderText("Type your message...") as HTMLTextAreaElement;
    const sendButton = screen.getByText("Send");

    await user.type(input, "Test message");
    await user.click(sendButton);

    expect(input.value).toBe("");
  });
});

