/**
 * Dashboard page component.
 * Placeholder for authenticated user dashboard.
 */
import React from "react";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/Button";
import { useNavigate } from "react-router-dom";

/**
 * Dashboard component.
 */
export const Dashboard: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome, {user?.username}!
          </h1>
          <p className="text-gray-600 mb-6">
            You are successfully authenticated. This is your dashboard.
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
          <Button onClick={handleLogout} variant="secondary">
            Logout
          </Button>
        </div>
      </div>
    </div>
  );
};

