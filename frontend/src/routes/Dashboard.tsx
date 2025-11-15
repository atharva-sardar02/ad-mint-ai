/**
 * Dashboard page component with prompt input form for video generation.
 */
import React, { useState, useEffect } from "react";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Textarea";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { useNavigate } from "react-router-dom";
import { generationService } from "../lib/generationService";

const MIN_PROMPT_LENGTH = 10;
const MAX_PROMPT_LENGTH = 500;

interface ValidationErrors {
  prompt?: string;
}

/**
 * Dashboard component with prompt input form for video generation.
 */
export const Dashboard: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const [prompt, setPrompt] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Real-time validation as user types.
   */
  useEffect(() => {
    const newErrors: ValidationErrors = {};

    if (prompt.trim() !== "") {
      if (prompt.length < MIN_PROMPT_LENGTH) {
        newErrors.prompt = `Prompt must be at least ${MIN_PROMPT_LENGTH} characters`;
      } else if (prompt.length > MAX_PROMPT_LENGTH) {
        newErrors.prompt = `Prompt must be no more than ${MAX_PROMPT_LENGTH} characters`;
      }
    }

    setErrors(newErrors);
    setApiError(""); // Clear API error when user types
  }, [prompt]);

  /**
   * Check if form is valid.
   */
  const isValid = prompt.length >= MIN_PROMPT_LENGTH && prompt.length <= MAX_PROMPT_LENGTH;

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate before submission
    if (!isValid) {
      setErrors({
        prompt: prompt.length < MIN_PROMPT_LENGTH
          ? `Prompt must be at least ${MIN_PROMPT_LENGTH} characters`
          : `Prompt must be no more than ${MAX_PROMPT_LENGTH} characters`,
      });
      return;
    }

    setIsLoading(true);
    setApiError("");
    setErrors({});

    try {
      const response = await generationService.startGeneration(prompt);
      // Navigate to generation status page
      navigate(`/generation/${response.generation_id}`);
    } catch (error: any) {
      setApiError(
        error?.message || "Failed to start video generation. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome, {user?.username}!
          </h1>
          <p className="text-gray-600 mb-6">
            Create professional video ads from simple text prompts.
          </p>
          {user && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                User Information
              </h2>
              <div className="space-y-2 text-sm text-gray-600">
                <p>
                  <strong>Username:</strong> {user.username}
                </p>
                {user.email && (
                  <p>
                    <strong>Email:</strong> {user.email}
                  </p>
                )}
                <p>
                  <strong>Total Generations:</strong> {user.total_generations}
                </p>
                <p>
                  <strong>Total Cost:</strong> ${user.total_cost.toFixed(2)}
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Create Video Ad
          </h2>
          <p className="text-gray-600 mb-6">
            Enter a description of the product or service you want to advertise.
            Our AI will create a professional video ad for you.
          </p>

          {/* Example Prompt */}
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-semibold text-blue-900 mb-2">Example Prompt:</p>
            <p className="text-sm text-blue-800 italic">
              "Create a 10 second ad for a Gauntlet water bottle"
            </p>
            <button
              type="button"
              onClick={() => setPrompt("Create a 10 second ad for a Gauntlet water bottle")}
              className="mt-2 text-sm text-blue-600 hover:text-blue-800 underline"
              disabled={isLoading}
            >
              Use this example
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Textarea
              label="Video Prompt"
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., Create a luxury watch ad for Instagram showcasing elegance and precision..."
              minLength={MIN_PROMPT_LENGTH}
              maxLength={MAX_PROMPT_LENGTH}
              rows={6}
              error={errors.prompt}
              helperText={`${prompt.length}/${MAX_PROMPT_LENGTH} characters (minimum ${MIN_PROMPT_LENGTH})`}
              disabled={isLoading}
              required
            />

            {apiError && (
              <ErrorMessage message={apiError} />
            )}

            <div className="flex gap-4">
              <Button
                type="submit"
                variant="primary"
                isLoading={isLoading}
                disabled={!isValid || isLoading}
                fullWidth
              >
                Generate Video
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={handleLogout}
                disabled={isLoading}
              >
                Logout
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

