/**
 * Unit tests for ParallelGenerationPanel component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ParallelGenerationPanel } from "../components/generation/ParallelGenerationPanel";

describe("ParallelGenerationPanel", () => {
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render parallel generation panel", () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} />
    );

    expect(screen.getByText("Parallel Generation Mode")).toBeInTheDocument();
    expect(screen.getByText("Settings Comparison")).toBeInTheDocument();
    expect(screen.getByText("Prompt Comparison")).toBeInTheDocument();
  });

  it("should allow switching between comparison modes", () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} />
    );

    const promptRadio = screen.getByLabelText("Prompt Comparison");
    fireEvent.click(promptRadio);

    expect(promptRadio).toBeChecked();
  });

  it("should allow selecting variation count", () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} />
    );

    const variationSelect = screen.getByLabelText(/Number of Variations/i);
    expect(variationSelect).toBeInTheDocument();
  });

  it("should show settings comparison mode UI when selected", () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} />
    );

    // Settings comparison is default
    expect(screen.getByLabelText(/Prompt \(shared across all variations\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Settings Profiles/i)).toBeInTheDocument();
  });

  it("should show prompt comparison mode UI when selected", () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} />
    );

    const promptRadio = screen.getByLabelText("Prompt Comparison");
    fireEvent.click(promptRadio);

    expect(screen.getByText(/Prompt Variations/i)).toBeInTheDocument();
    expect(screen.getByText(/Coherence Settings \(shared across all prompts\)/i)).toBeInTheDocument();
  });

  it("should validate prompt length in settings comparison mode", async () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} />
    );

    const promptInput = screen.getByLabelText(/Prompt \(shared across all variations\)/i);
    fireEvent.change(promptInput, { target: { value: "short" } });

    const submitButton = screen.getByRole("button", { name: /Generate.*Variations/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  it("should call onSubmit with correct data when form is valid", async () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} />
    );

    const promptInput = screen.getByLabelText(/Prompt \(shared across all variations\)/i);
    fireEvent.change(promptInput, { target: { value: "This is a valid prompt for testing parallel generation" } });

    const submitButton = screen.getByRole("button", { name: /Generate.*Variations/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled();
      const callArgs = mockOnSubmit.mock.calls[0];
      expect(callArgs[0]).toHaveLength(2); // 2 variations
      expect(callArgs[0][0].prompt).toBe("This is a valid prompt for testing parallel generation");
      expect(callArgs[1]).toBe("settings"); // comparison type
    });
  });

  it("should call onCancel when cancel button is clicked", () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} />
    );

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it("should disable form when isLoading is true", () => {
    render(
      <ParallelGenerationPanel onSubmit={mockOnSubmit} onCancel={mockOnCancel} isLoading={true} />
    );

    const submitButton = screen.getByText(/Starting Generation/i);
    expect(submitButton).toBeDisabled();
  });

  it("should display error message when provided", () => {
    const errorMessage = "Failed to start parallel generation";
    render(
      <ParallelGenerationPanel
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
        error={errorMessage}
      />
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });
});

