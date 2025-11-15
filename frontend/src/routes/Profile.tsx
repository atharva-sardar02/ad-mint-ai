/**
 * Profile page component.
 * Placeholder for user profile (will be fully implemented in Epic 5).
 */
import React from "react";
import { useAuthStore } from "../store/authStore";

export const Profile: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome to Profile
          </h1>
          <p className="text-gray-600 mb-6">
            This is a placeholder for the user profile feature. It will be
            fully implemented in Epic 5.
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
      </div>
    </div>
  );
};

