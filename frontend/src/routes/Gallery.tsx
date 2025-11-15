/**
 * Gallery page component.
 * Placeholder for video gallery (will be fully implemented in Epic 4).
 */
import React from "react";
import { useAuthStore } from "../store/authStore";

export const Gallery: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome to Gallery
          </h1>
          <p className="text-gray-600 mb-6">
            This is a placeholder for the video gallery feature. It will be
            fully implemented in Epic 4.
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
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

