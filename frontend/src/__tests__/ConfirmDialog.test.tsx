/**
 * Unit tests for ConfirmDialog component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";

describe("ConfirmDialog", () => {
  const mockOnConfirm = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with correct title and message (AC-4.3.2)", () => {
    render(
      <ConfirmDialog
        title="Delete Video"
        message="Are you sure you want to delete this video? This action cannot be undone."
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={true}
      />
    );

    expect(screen.getByText("Delete Video")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Are you sure you want to delete this video? This action cannot be undone."
      )
    ).toBeInTheDocument();
  });

  it("should not render when isOpen is false", () => {
    render(
      <ConfirmDialog
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={false}
      />
    );

    expect(screen.queryByText("Test message")).not.toBeInTheDocument();
  });

  it("should call onConfirm when confirm button is clicked (AC-4.3.2)", () => {
    render(
      <ConfirmDialog
        message="Test message"
        confirmText="Delete"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={true}
      />
    );

    const confirmButton = screen.getByText("Delete");
    fireEvent.click(confirmButton);

    expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    expect(mockOnCancel).not.toHaveBeenCalled();
  });

  it("should call onCancel when cancel button is clicked (AC-4.3.2)", () => {
    render(
      <ConfirmDialog
        message="Test message"
        cancelText="Cancel"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={true}
      />
    );

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  it("should call onCancel when escape key is pressed (AC-4.3.2)", () => {
    render(
      <ConfirmDialog
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={true}
      />
    );

    fireEvent.keyDown(document, { key: "Escape" });

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  it("should call onCancel when backdrop is clicked", () => {
    render(
      <ConfirmDialog
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={true}
      />
    );

    const backdrop = screen.getByRole("dialog").parentElement?.querySelector(
      ".fixed.inset-0.bg-black"
    );
    if (backdrop) {
      fireEvent.click(backdrop);
      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    }
  });

  it("should use default title when not provided", () => {
    render(
      <ConfirmDialog
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={true}
      />
    );

    expect(screen.getByText("Confirm Action")).toBeInTheDocument();
  });

  it("should use default button texts when not provided", () => {
    render(
      <ConfirmDialog
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={true}
      />
    );

    expect(screen.getByText("Confirm")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("should have proper ARIA attributes for accessibility", () => {
    render(
      <ConfirmDialog
        title="Delete Video"
        message="Test message"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        isOpen={true}
      />
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "dialog-title");
    expect(dialog).toHaveAttribute("aria-describedby", "dialog-message");
  });
});



