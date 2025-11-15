/**
 * Registration page component.
 * Implements registration form with real-time validation, loading states, and error handling.
 */
import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { ErrorMessage } from "../../components/ui/ErrorMessage";
import { useAuthStore } from "../../store/authStore";

/**
 * Validation rules for registration form.
 */
const USERNAME_REGEX = /^[a-zA-Z0-9_]+$/;
const MIN_USERNAME_LENGTH = 3;
const MAX_USERNAME_LENGTH = 50;
const MIN_PASSWORD_LENGTH = 8;

/**
 * Validation errors interface.
 */
interface ValidationErrors {
  username?: string;
  password?: string;
  email?: string;
}

/**
 * Registration component.
 */
export const Register: React.FC = () => {
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);

  const [formData, setFormData] = useState({
    username: "",
    password: "",
    email: "",
  });

  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  /**
   * Real-time validation as user types.
   */
  useEffect(() => {
    const newErrors: ValidationErrors = {};

    // Username validation
    if (formData.username) {
      if (formData.username.length < MIN_USERNAME_LENGTH) {
        newErrors.username = `Username must be at least ${MIN_USERNAME_LENGTH} characters`;
      } else if (formData.username.length > MAX_USERNAME_LENGTH) {
        newErrors.username = `Username must be no more than ${MAX_USERNAME_LENGTH} characters`;
      } else if (!USERNAME_REGEX.test(formData.username)) {
        newErrors.username =
          "Username can only contain letters, numbers, and underscores";
      }
    }

    // Password validation
    if (formData.password) {
      if (formData.password.length < MIN_PASSWORD_LENGTH) {
        newErrors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters`;
      }
    }

    // Email validation (optional, but if provided, should be valid)
    if (formData.email && formData.email.trim() !== "") {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        newErrors.email = "Please enter a valid email address";
      }
    }

    setErrors(newErrors);
    setApiError(""); // Clear API error when user types
  }, [formData]);

  /**
   * Check if form is valid.
   */
  const isFormValid = (): boolean => {
    return (
      formData.username.length >= MIN_USERNAME_LENGTH &&
      formData.username.length <= MAX_USERNAME_LENGTH &&
      USERNAME_REGEX.test(formData.username) &&
      formData.password.length >= MIN_PASSWORD_LENGTH &&
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
      await register(
        formData.username,
        formData.password,
        formData.email.trim() || undefined
      );

      // Show success message
      setShowSuccess(true);

      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (error) {
      setApiError(
        error instanceof Error ? error.message : "Registration failed"
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
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{" "}
            <Link
              to="/login"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              sign in to your existing account
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {showSuccess && (
            <div
              className="p-3 rounded-md bg-green-50 border border-green-200 text-sm text-green-800"
              role="alert"
            >
              Account created successfully! Redirecting to login...
            </div>
          )}

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
              placeholder="Enter username (3-50 characters)"
            />

            <Input
              label="Password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              error={errors.password}
              required
              autoComplete="new-password"
              placeholder="Enter password (min 8 characters)"
            />

            <Input
              label="Email (optional)"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              autoComplete="email"
              placeholder="Enter email address"
            />
          </div>

          <div>
            <Button
              type="submit"
              fullWidth
              isLoading={isLoading}
              disabled={!isFormValid() || isLoading || showSuccess}
            >
              Create Account
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

