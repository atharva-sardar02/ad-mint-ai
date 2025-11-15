/**
 * Login page component.
 * Implements login form with validation, token storage, auth store update, and redirect to dashboard.
 */
import React, { useState, useEffect } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { ErrorMessage } from "../../components/ui/ErrorMessage";
import { useAuthStore } from "../../store/authStore";

/**
 * Validation errors interface.
 */
interface ValidationErrors {
  username?: string;
  password?: string;
}

/**
 * Login component.
 */
export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((state) => state.login);

  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });

  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Real-time validation as user types.
   */
  useEffect(() => {
    const newErrors: ValidationErrors = {};

    // Username validation (non-empty)
    if (formData.username.trim() === "" && formData.username.length > 0) {
      newErrors.username = "Username is required";
    }

    // Password validation (non-empty)
    if (formData.password === "" && formData.password.length > 0) {
      newErrors.password = "Password is required";
    }

    setErrors(newErrors);
    setApiError(""); // Clear API error when user types
  }, [formData]);

  /**
   * Check if form is valid.
   */
  const isFormValid = (): boolean => {
    return (
      formData.username.trim() !== "" &&
      formData.password !== "" &&
      Object.keys(errors).length === 0
    );
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setApiError("");

    if (!isFormValid()) {
      return;
    }

    setIsLoading(true);

    try {
      await login(formData.username, formData.password);

      // Redirect to saved URL or default to dashboard
      const from = (location.state as { from?: string })?.from || "/dashboard";
      navigate(from, { replace: true });
    } catch (error) {
      setApiError(
        error instanceof Error ? error.message : "Invalid username or password"
      );
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle input change.
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{" "}
            <Link
              to="/register"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              create a new account
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {apiError && <ErrorMessage message={apiError} />}

          <div className="space-y-4">
            <Input
              label="Username"
              name="username"
              type="text"
              value={formData.username}
              onChange={handleChange}
              error={errors.username}
              required
              autoComplete="username"
              placeholder="Enter your username"
            />

            <Input
              label="Password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              error={errors.password}
              required
              autoComplete="current-password"
              placeholder="Enter your password"
            />
          </div>

          <div>
            <Button
              type="submit"
              fullWidth
              isLoading={isLoading}
              disabled={!isFormValid() || isLoading}
            >
              Sign In
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

