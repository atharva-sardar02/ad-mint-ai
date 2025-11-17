/**
 * Unit tests for Dashboard component prompt validation.
 * Tests prompt input validation with various lengths and edge cases.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Dashboard } from "../routes/Dashboard";
import { useAuthStore } from "../store/authStore";
import { generationService } from "../lib/generationService";

// Mock generationService
vi.mock("../lib/generationService", () => ({
  generationService: {
    startGeneration: vi.fn(),
    startGenerationWithImage: vi.fn(),
    getGenerationStatus: vi.fn(),
    getCoherenceSettingsDefaults: vi.fn().mockResolvedValue({
      seed_control: true,
      ip_adapter_reference: false,
      ip_adapter_sequential: false,
      lora: false,
      enhanced_planning: true,
      vbench_quality_control: true,
      post_processing_enhancement: true,
      controlnet: false,
      csfd_detection: false,
    }),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("Dashboard Prompt Validation", () => {
  beforeEach(() => {
    // Set authenticated user
    useAuthStore.setState({
      isAuthenticated: true,
      user: {
        id: "1",
        username: "testuser",
        email: "test@example.com",
        total_generations: 0,
        total_cost: 0,
      },
      token: "test-token",
    });
    vi.clearAllMocks();
  });

  it("should show error for prompt shorter than 10 characters", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });

    // Enter short prompt (9 characters)
    fireEvent.change(textarea, { target: { value: "short" } });

    // Wait for validation
    await waitFor(() => {
      expect(screen.getByText(/must be at least 10 characters/i)).toBeInTheDocument();
    });

    // Submit button should be disabled
    expect(submitButton).toBeDisabled();
  });

  it("should show error for prompt longer than 500 characters", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const longPrompt = "a".repeat(501);

    fireEvent.change(textarea, { target: { value: longPrompt } });

    await waitFor(() => {
      expect(screen.getByText(/must be no more than 500 characters/i)).toBeInTheDocument();
    });

    const submitButton = screen.getByRole("button", { name: /generate video/i });
    expect(submitButton).toBeDisabled();
  });

  it("should accept valid prompt (10 characters)", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const validPrompt = "a".repeat(10);

    fireEvent.change(textarea, { target: { value: validPrompt } });

    await waitFor(() => {
      const submitButton = screen.getByRole("button", { name: /generate video/i });
      expect(submitButton).not.toBeDisabled();
    });

    // Should not show error
    expect(screen.queryByText(/must be at least/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/must be no more than/i)).not.toBeInTheDocument();
  });

  it("should accept valid prompt (500 characters)", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const validPrompt = "a".repeat(500);

    fireEvent.change(textarea, { target: { value: validPrompt } });

    await waitFor(() => {
      const submitButton = screen.getByRole("button", { name: /generate video/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  it("should show character count helper text", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    fireEvent.change(textarea, { target: { value: "test prompt" } });

    expect(screen.getByText(/11\/500 characters/i)).toBeInTheDocument();
  });

  it("should clear error when valid prompt is entered", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);

    // Enter invalid prompt
    fireEvent.change(textarea, { target: { value: "short" } });

    await waitFor(() => {
      expect(screen.getByText(/must be at least 10 characters/i)).toBeInTheDocument();
    });

    // Enter valid prompt
    fireEvent.change(textarea, { target: { value: "valid prompt here" } });

    await waitFor(() => {
      expect(screen.queryByText(/must be at least 10 characters/i)).not.toBeInTheDocument();
    });
  });

  it("should disable submit button when prompt is invalid", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });

    // Invalid prompt
    fireEvent.change(textarea, { target: { value: "short" } });

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });

  it("should enable submit button when prompt is valid", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });

    // Valid prompt
    fireEvent.change(textarea, { target: { value: "This is a valid prompt that is long enough" } });

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  it("should prevent form submission with invalid prompt", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const form = textarea.closest("form");

    // Enter invalid prompt
    fireEvent.change(textarea, { target: { value: "short" } });

    await waitFor(() => {
      const submitButton = screen.getByRole("button", { name: /generate video/i });
      expect(submitButton).toBeDisabled();
    });

    // Try to submit
    if (form) {
      fireEvent.submit(form);
    }

    // Should not call generationService
    expect(generationService.startGeneration).not.toHaveBeenCalled();
  });

  describe("Reference Image Upload", () => {
    it("should reject invalid image file type", async () => {
      render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      );

      const fileInput = screen.getByLabelText(/reference image/i) as HTMLInputElement;
      expect(fileInput).toBeInTheDocument();

      const invalidFile = new File(["test"], "test.pdf", { type: "application/pdf" });
      fireEvent.change(fileInput, { target: { files: [invalidFile] } });

      expect(
        await screen.findByText(/only JPG and PNG images are allowed/i)
      ).toBeInTheDocument();
    });

    it("should reject image file larger than 10MB", async () => {
      render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      );

      const fileInput = screen.getByLabelText(/reference image/i) as HTMLInputElement;

      const largeFile = new File(
        ["a".repeat(11 * 1024 * 1024)],
        "large.jpg",
        { type: "image/jpeg" }
      );

      fireEvent.change(fileInput, { target: { files: [largeFile] } });

      expect(
        await screen.findByText(/image size must be less than 10MB/i)
      ).toBeInTheDocument();
    });

    it("should accept valid JPG image and show preview", async () => {
      render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      );

      // Mock URL.createObjectURL for preview
      const createObjectURLSpy = vi
        .spyOn(URL, "createObjectURL")
        .mockReturnValue("blob:preview");

      const fileInput = screen.getByLabelText(/reference image/i) as HTMLInputElement;

      const validFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
      fireEvent.change(fileInput, { target: { files: [validFile] } });

      const preview = await screen.findByAltText(/reference preview/i);
      expect(preview).toBeInTheDocument();

      createObjectURLSpy.mockRestore();
    });

    it("should remove image when remove button is clicked", async () => {
      render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      );

      const createObjectURLSpy = vi
        .spyOn(URL, "createObjectURL")
        .mockReturnValue("blob:preview");

      const fileInput = screen.getByLabelText(/reference image/i) as HTMLInputElement;

      const validFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
      fireEvent.change(fileInput, { target: { files: [validFile] } });

      expect(await screen.findByAltText(/reference preview/i)).toBeInTheDocument();

      const removeButton = screen.getByRole("button", { name: /remove image/i });
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(screen.queryByAltText(/reference preview/i)).not.toBeInTheDocument();
        expect(fileInput.value).toBe("");
      });

      createObjectURLSpy.mockRestore();
    });
  });
});



