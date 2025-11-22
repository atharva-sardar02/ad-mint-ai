/**
 * LLM Conversation History Display
 * 
 * Shows the complete LLM conversation history for a Master Mode generation.
 * Used on the video detail page to review all agent interactions after generation.
 */
import React, { useEffect, useState } from "react";
import apiClient from "../../lib/apiClient";

interface LLMInteraction {
  type: "llm_interaction";
  agent: string;
  interaction_type: "prompt" | "response";
  content: string;
  metadata: Record<string, any>;
  timestamp: string;
}

interface ConversationHistoryProps {
  generationId: string;
}

export const ConversationHistory: React.FC<ConversationHistoryProps> = ({
  generationId,
}) => {
  const [interactions, setInteractions] = useState<LLMInteraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    const fetchConversation = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const response = await apiClient.get(
          `${apiUrl}/api/master-mode/conversation/${generationId}`
        );
        
        if (response.data.conversation) {
          setInteractions(response.data.conversation);
        }
      } catch (err: any) {
        console.error("Failed to load conversation history:", err);
        setError(err.message || "Failed to load conversation");
      } finally {
        setLoading(false);
      }
    };

    fetchConversation();
  }, [generationId]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading conversation history...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 text-sm">⚠️ {error}</p>
      </div>
    );
  }

  if (interactions.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-gray-600 text-sm">
          No conversation history available for this generation.
        </p>
      </div>
    );
  }

  const getAgentColor = (agent: string): string => {
    if (agent.includes("Director")) return "bg-purple-100 text-purple-800";
    if (agent.includes("Critic")) return "bg-orange-100 text-orange-800";
    if (agent.includes("Writer")) return "bg-blue-100 text-blue-800";
    if (agent.includes("Cohesor")) return "bg-green-100 text-green-800";
    if (agent.includes("Enhancer")) return "bg-indigo-100 text-indigo-800";
    if (agent.includes("Aligner")) return "bg-teal-100 text-teal-800";
    if (agent.includes("Sanitizer")) return "bg-pink-100 text-pink-800";
    return "bg-gray-100 text-gray-800";
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header */}
      <div
        className="p-4 bg-gradient-to-r from-purple-600 to-blue-600 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">
              🤖 LLM Conversation History
            </h3>
            <p className="text-sm text-purple-100 mt-1">
              {interactions.length} agent interactions recorded
            </p>
          </div>
          <button className="text-white hover:text-purple-100 transition-colors">
            <svg
              className={`w-6 h-6 transform transition-transform ${
                isExpanded ? "rotate-180" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Conversation List */}
      {isExpanded && (
        <div className="p-4 max-h-[600px] overflow-y-auto">
          <div className="space-y-4">
            {interactions.map((interaction, idx) => (
              <div
                key={idx}
                className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
              >
                {/* Agent Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${getAgentColor(
                        interaction.agent
                      )}`}
                    >
                      {interaction.agent}
                    </span>
                    {interaction.interaction_type === "prompt" && (
                      <span className="text-xs text-gray-500">→ Prompt</span>
                    )}
                    {interaction.interaction_type === "response" && (
                      <span className="text-xs text-gray-500">← Response</span>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {formatTimestamp(interaction.timestamp)}
                  </span>
                </div>

                {/* Metadata Badges */}
                {interaction.metadata && Object.keys(interaction.metadata).length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {interaction.metadata.iteration !== undefined && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        Iteration {interaction.metadata.iteration}
                      </span>
                    )}
                    {interaction.metadata.scene_number !== undefined && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        Scene {interaction.metadata.scene_number}
                      </span>
                    )}
                    {interaction.metadata.score !== undefined && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                        Score: {interaction.metadata.score}/100
                      </span>
                    )}
                    {interaction.metadata.status && (
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          interaction.metadata.status === "approved"
                            ? "bg-green-100 text-green-700"
                            : "bg-yellow-100 text-yellow-700"
                        }`}
                      >
                        {interaction.metadata.status}
                      </span>
                    )}
                  </div>
                )}

                {/* Content */}
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700 bg-gray-50 p-3 rounded">
                    {interaction.content}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      {isExpanded && (
        <div className="p-3 bg-gray-50 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center">
            This conversation was recorded during video generation and can be viewed anytime.
          </p>
        </div>
      )}
    </div>
  );
};

