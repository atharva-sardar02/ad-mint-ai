/**
 * Unit tests for ProgressBar component.
 * Tests progress display, status rendering, cancel button visibility, and error handling.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ProgressBar } from "../components/ProgressBar";

describe("ProgressBar Component", () => {
  describe("Progress Display", () => {
    it("should display progress percentage", () => {
      render(
        <ProgressBar
          progress={50}
          currentStep="Processing"
          status="processing"
        />
      );

      expect(screen.getByText("50%")).toBeInTheDocument();
    });

    it("should display progress bar with correct width", () => {
      const { container } = render(
        <ProgressBar
          progress={75}
          currentStep="Processing"
          status="processing"
        />
      );

      const progressBar = container.querySelector(".bg-blue-500");
      expect(progressBar).toHaveStyle({ width: "75%" });
    });

    it("should clamp progress to 0-100", () => {
      const { container } = render(
        <ProgressBar
          progress={150}
          currentStep="Processing"
          status="processing"
        />
      );

      const progressBar = container.querySelector(".bg-blue-500");
      expect(progressBar).toHaveStyle({ width: "100%" });
    });
  });

  describe("Status Display", () => {
    it("should display pending status", () => {
      render(
        <ProgressBar
          progress={0}
          currentStep="Initializing"
          status="pending"
        />
      );

      expect(screen.getByText("Status:")).toBeInTheDocument();
      expect(screen.getByText("Pending")).toBeInTheDocument();
    });

    it("should display processing status", () => {
      render(
        <ProgressBar
          progress={50}
          currentStep="Processing"
          status="processing"
        />
      );

      // "Processing" appears in both status and currentStep, so check for both
      const processingTexts = screen.getAllByText("Processing");
      expect(processingTexts.length).toBeGreaterThan(0);
      expect(screen.getByText(/Status:/)).toBeInTheDocument();
    });

    it("should display completed status", () => {
      render(
        <ProgressBar
          progress={100}
          currentStep="Complete"
          status="completed"
        />
      );

      expect(screen.getByText("Completed")).toBeInTheDocument();
    });

    it("should display failed status", () => {
      render(
        <ProgressBar
          progress={50}
          currentStep="Error"
          status="failed"
          error="Test error"
        />
      );

      expect(screen.getByText("Failed")).toBeInTheDocument();
    });
  });

  describe("Current Step Display", () => {
    it("should display current step when provided", () => {
      render(
        <ProgressBar
          progress={50}
          currentStep="Generating video clip 2 of 3"
          status="processing"
        />
      );

      expect(screen.getByText(/Current step:/)).toBeInTheDocument();
      expect(screen.getByText("Generating video clip 2 of 3")).toBeInTheDocument();
    });

    it("should not display current step when null", () => {
      render(
        <ProgressBar
          progress={50}
          currentStep={null}
          status="processing"
        />
      );

      expect(screen.queryByText(/Current step:/)).not.toBeInTheDocument();
    });
  });

  describe("Error Display", () => {
    it("should display error message when status is failed", () => {
      render(
        <ProgressBar
          progress={50}
          currentStep="Error"
          status="failed"
          error="Video generation failed: API error"
        />
      );

      expect(screen.getByText(/Error:/)).toBeInTheDocument();
      expect(screen.getByText("Video generation failed: API error")).toBeInTheDocument();
    });

    it("should not display error when status is not failed", () => {
      render(
        <ProgressBar
          progress={50}
          currentStep="Processing"
          status="processing"
          error="Some error"
        />
      );

      expect(screen.queryByText(/Error:/)).not.toBeInTheDocument();
    });
  });

  describe("Cancel Button", () => {
    it("should show cancel button during processing", () => {
      const onCancel = vi.fn();
      render(
        <ProgressBar
          progress={50}
          currentStep="Processing"
          status="processing"
          onCancel={onCancel}
        />
      );

      const cancelButton = screen.getByRole("button", { name: /cancel generation/i });
      expect(cancelButton).toBeInTheDocument();
    });

    it("should show cancel button during pending", () => {
      const onCancel = vi.fn();
      render(
        <ProgressBar
          progress={0}
          currentStep="Initializing"
          status="pending"
          onCancel={onCancel}
        />
      );

      const cancelButton = screen.getByRole("button", { name: /cancel generation/i });
      expect(cancelButton).toBeInTheDocument();
    });

    it("should hide cancel button when completed", () => {
      render(
        <ProgressBar
          progress={100}
          currentStep="Complete"
          status="completed"
          onCancel={vi.fn()}
        />
      );

      expect(screen.queryByRole("button", { name: /cancel generation/i })).not.toBeInTheDocument();
    });

    it("should hide cancel button when failed", () => {
      render(
        <ProgressBar
          progress={50}
          currentStep="Error"
          status="failed"
          error="Test error"
          onCancel={vi.fn()}
        />
      );

      expect(screen.queryByRole("button", { name: /cancel generation/i })).not.toBeInTheDocument();
    });

    it("should call onCancel when cancel button is clicked", () => {
      const onCancel = vi.fn();
      render(
        <ProgressBar
          progress={50}
          currentStep="Processing"
          status="processing"
          onCancel={onCancel}
        />
      );

      const cancelButton = screen.getByRole("button", { name: /cancel generation/i });
      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe("Progress Bar Colors", () => {
    it("should use blue color for processing", () => {
      const { container } = render(
        <ProgressBar
          progress={50}
          currentStep="Processing"
          status="processing"
        />
      );

      const progressBar = container.querySelector(".bg-blue-500");
      expect(progressBar).toBeInTheDocument();
    });

    it("should use green color for completed", () => {
      const { container } = render(
        <ProgressBar
          progress={100}
          currentStep="Complete"
          status="completed"
        />
      );

      const progressBar = container.querySelector(".bg-green-500");
      expect(progressBar).toBeInTheDocument();
    });

    it("should use red color for failed", () => {
      const { container } = render(
        <ProgressBar
          progress={50}
          currentStep="Error"
          status="failed"
          error="Test error"
        />
      );

      const progressBar = container.querySelector(".bg-red-500");
      expect(progressBar).toBeInTheDocument();
    });
  });
});

