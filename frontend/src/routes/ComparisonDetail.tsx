/**
 * ComparisonDetail page component for viewing parallel generation comparison results.
 */
import React from "react";
import { useParams } from "react-router-dom";
import { ComparisonView } from "../components/generation";

/**
 * ComparisonDetail page component.
 */
export const ComparisonDetail: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();

  if (!groupId) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6">
            <p className="text-red-600">Invalid comparison group ID</p>
          </div>
        </div>
      </div>
    );
  }

  return <ComparisonView groupId={groupId} />;
};

