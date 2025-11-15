/**
 * Profile page component.
 * Displays user information and statistics.
 */
import React, { useEffect, useState } from "react";
import { useAuthStore } from "../store/authStore";
import { getUserProfile } from "../lib/userService";
import type { UserProfile } from "../lib/types/api";
import { Button } from "../components/ui/Button";

/**
 * Format account creation date as "Member since: {month} {year}".
 */
function formatMemberSince(dateString: string): string {
  const date = new Date(dateString);
  const month = date.toLocaleDateString("en-US", { month: "short" });
  const year = date.getFullYear();
  return `Member since: ${month} ${year}`;
}

/**
 * Format cost as currency (e.g., "$24.50").
 */
function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format last login as relative time (e.g., "2 hours ago", "3 days ago").
 */
function formatRelativeTime(dateString: string | null): string {
  if (!dateString) {
    return "Never";
  }

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "Just now";
  } else if (diffMinutes < 60) {
    return `${diffMinutes} ${diffMinutes === 1 ? "minute" : "minutes"} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? "hour" : "hours"} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} ${diffDays === 1 ? "day" : "days"} ago`;
  } else {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} ${weeks === 1 ? "week" : "weeks"} ago`;
  }
}

export const Profile: React.FC = () => {
  const { logout } = useAuthStore();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getUserProfile();
        setProfile(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load profile";
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleLogout = () => {
    logout();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-600">Loading profile...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="text-center py-12">
              <div className="text-red-600 mb-4">
                <svg
                  className="mx-auto h-12 w-12"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Error Loading Profile
              </h2>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button
                variant="primary"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-8 sm:px-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              {profile.username}
            </h1>
            {profile.email && (
              <p className="text-blue-100 text-lg">{profile.email}</p>
            )}
            <p className="text-blue-200 mt-2">
              {formatMemberSince(profile.created_at)}
            </p>
          </div>

          {/* Content */}
          <div className="px-6 py-8 sm:px-8">
            {/* Statistics Section */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                Statistics
              </h2>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="text-sm font-medium text-gray-500 mb-1">
                    Total Videos Generated
                  </div>
                  <div className="text-3xl font-bold text-gray-900">
                    {profile.total_generations}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="text-sm font-medium text-gray-500 mb-1">
                    Total Cost Spent
                  </div>
                  <div className="text-3xl font-bold text-gray-900">
                    {formatCurrency(profile.total_cost)}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="text-sm font-medium text-gray-500 mb-1">
                    Last Login
                  </div>
                  <div className="text-lg font-semibold text-gray-900">
                    {formatRelativeTime(profile.last_login)}
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="border-t border-gray-200 pt-6">
              <Button variant="secondary" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
