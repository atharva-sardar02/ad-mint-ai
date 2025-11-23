/**
 * Component tests for QuickActions (Story 1.3)
 * Tests approve/regenerate buttons for checkpoints
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QuickActions } from "../QuickActions";

describe("QuickActions Component", () => {
  it("should render approve and regenerate buttons", () => {
    const onApprove = vi.fn();
    const onRegenerate = vi.fn();

    render(
      <QuickActions onApprove={onApprove} onRegenerate={onRegenerate} />
    );

    expect(screen.getByText("Regenerate")).toBeInTheDocument();
    expect(screen.getByText("✓ Approve & Continue")).toBeInTheDocument();
  });

  it("should call onApprove when approve button clicked", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    const onRegenerate = vi.fn();

    render(
      <QuickActions onApprove={onApprove} onRegenerate={onRegenerate} />
    );

    const approveButton = screen.getByText("✓ Approve & Continue");
    await user.click(approveButton);

    expect(onApprove).toHaveBeenCalledTimes(1);
  });

  it("should call onRegenerate when regenerate button clicked", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    const onRegenerate = vi.fn();

    render(
      <QuickActions onApprove={onApprove} onRegenerate={onRegenerate} />
    );

    const regenerateButton = screen.getByText("Regenerate");
    await user.click(regenerateButton);

    expect(onRegenerate).toHaveBeenCalledTimes(1);
  });

  it("should show 'Regenerating...' text when isRegenerating is true", () => {
    const onApprove = vi.fn();
    const onRegenerate = vi.fn();

    render(
      <QuickActions
        onApprove={onApprove}
        onRegenerate={onRegenerate}
        isRegenerating={true}
      />
    );

    expect(screen.getByText("Regenerating...")).toBeInTheDocument();
  });

  it("should disable buttons when disabled prop is true", () => {
    const onApprove = vi.fn();
    const onRegenerate = vi.fn();

    render(
      <QuickActions
        onApprove={onApprove}
        onRegenerate={onRegenerate}
        disabled={true}
      />
    );

    const approveButton = screen.getByText("✓ Approve & Continue");
    const regenerateButton = screen.getByText("Regenerate");

    expect(approveButton).toBeDisabled();
    expect(regenerateButton).toBeDisabled();
  });

  it("should disable buttons when isRegenerating is true", () => {
    const onApprove = vi.fn();
    const onRegenerate = vi.fn();

    render(
      <QuickActions
        onApprove={onApprove}
        onRegenerate={onRegenerate}
        isRegenerating={true}
      />
    );

    const approveButton = screen.getByText("✓ Approve & Continue");
    const regenerateButton = screen.getByText("Regenerating...");

    expect(approveButton).toBeDisabled();
    expect(regenerateButton).toBeDisabled();
  });
});

