/**
 * LLM Conversation Viewer Component
 * 
 * Displays real-time LLM interactions (prompts and responses) as they happen.
 */
import React, { useEffect, useState, useRef } from "react";

interface LLMInteraction {
  type: "llm_interaction";
  agent: string;
  interaction_type: "prompt" | "response";
  content: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

interface ProgressUpdate {
  step?: string;
  status?: string;
  progress?: number;
  message?: string;
  data?: any;
}

type StreamUpdate = LLMInteraction | ProgressUpdate;

interface LLMConversationViewerProps {
  generationId: string;
  onComplete?: (data: { 
    finalVideoPath?: string; 
    sceneVideos?: string[];
    numScenes?: number;
    cohesionScore?: number;
    storyScore?: number;
  }) => void;
  onError?: (error: string) => void;
}

export const LLMConversationViewer: React.FC<LLMConversationViewerProps> = ({
  generationId,
  onComplete,
  onError,
}) => {
  const [interactions, setInteractions] = useState<LLMInteraction[]>([]);
  const [currentStep, setCurrentStep] = useState("Initializing...");
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const conversationEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new interactions arrive
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [interactions]);

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    
    // EventSource doesn't support custom headers, but should send cookies automatically
    // Make sure the URL includes credentials
    const eventSource = new EventSource(
      `${apiUrl}/api/master-mode/progress/${generationId}`,
      { withCredentials: true }
    );

    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 3;

    eventSource.onmessage = (event) => {
      reconnectAttempts = 0; // Reset on successful message
      
      try {
        const update: StreamUpdate = JSON.parse(event.data);

        // Check if it's an LLM interaction
        if ("type" in update && update.type === "llm_interaction") {
          const interaction = update as LLMInteraction;
          setInteractions((prev) => [...prev, interaction]);
        } else {
          // It's a progress update
          const progressUpdate = update as ProgressUpdate;
          if (progressUpdate.message) {
            setCurrentStep(progressUpdate.message);
          }
          if (progressUpdate.progress !== undefined) {
            setProgress(progressUpdate.progress);
          }

          // Check if complete
          if (progressUpdate.step === "complete") {
            setIsComplete(true);
            eventSource.close();
            if (onComplete && progressUpdate.data) {
              onComplete({
                finalVideoPath: progressUpdate.data.final_video_path,
                sceneVideos: progressUpdate.data.scene_videos,
                numScenes: progressUpdate.data.num_scenes,
                cohesionScore: progressUpdate.data.cohesion_score,
                storyScore: progressUpdate.data.story_score,
              });
            }
          }

          // Check if failed
          if (progressUpdate.status === "failed") {
            eventSource.close();
            if (onError && progressUpdate.message) {
              onError(progressUpdate.message);
            }
          }
        }
      } catch (error) {
        console.error("Error parsing SSE message:", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE connection error:", error);
      
      reconnectAttempts++;
      
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        eventSource.close();
        if (onError) {
          onError("Connection to server lost. Please refresh the page or check the gallery.");
        }
      }
    };

    return () => {
      eventSource.close();
    };
  }, [generationId, onComplete, onError]);

  const getAgentColor = (agent: string): string => {
    if (agent.includes("Director")) return "blue";
    if (agent.includes("Critic")) return "purple";
    if (agent.includes("Writer")) return "blue";
    if (agent.includes("Cohesor")) return "green";
    return "gray";
  };

  const getAgentBgColor = (agent: string): string => {
    const color = getAgentColor(agent);
    const colors: Record<string, string> = {
      blue: "bg-blue-50 border-blue-200",
      purple: "bg-purple-50 border-purple-200",
      green: "bg-green-50 border-green-200",
      gray: "bg-gray-50 border-gray-200",
    };
    return colors[color] || colors.gray;
  };

  const getAgentTextColor = (agent: string): string => {
    const color = getAgentColor(agent);
    const colors: Record<string, string> = {
      blue: "text-blue-700",
      purple: "text-purple-700",
      green: "text-green-700",
      gray: "text-gray-700",
    };
    return colors[color] || colors.gray;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">AI Agent Conversation</h2>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">{currentStep}</span>
          <span className="text-sm font-medium text-gray-700">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Conversation Timeline */}
      <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
        {interactions.length === 0 && !isComplete && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-500">Waiting for AI agents to start conversation...</p>
          </div>
        )}

        {interactions.map((interaction, idx) => {
          const agentColor = getAgentBgColor(interaction.agent);
          const textColor = getAgentTextColor(interaction.agent);

          return (
            <div key={idx} className="animate-fadeIn">
              {/* Agent Header */}
              <div className={`flex items-center gap-2 mb-2`}>
                <div className={`w-8 h-8 rounded-full ${agentColor} flex items-center justify-center`}>
                  <span className={`text-sm font-bold ${textColor}`}>
                    {interaction.agent.charAt(0)}
                  </span>
                </div>
                <div>
                  <h3 className={`font-semibold ${textColor}`}>{interaction.agent}</h3>
                  <p className="text-xs text-gray-500">
                    {new Date(interaction.timestamp).toLocaleTimeString()}
                    {interaction.metadata?.iteration && ` • Iteration ${interaction.metadata.iteration}`}
                    {interaction.metadata?.score && ` • Score: ${interaction.metadata.score}/100`}
                  </p>
                </div>
              </div>

              {/* Message Content */}
              <div className={`ml-10 p-4 rounded-lg border-2 ${agentColor}`}>
                <div className="prose prose-sm max-w-none">
                  {interaction.content.split('\n').map((line, lineIdx) => {
                    // Format markdown-like text
                    if (line.startsWith('**') && line.endsWith('**')) {
                      return (
                        <p key={lineIdx} className="font-bold text-gray-900 mb-1">
                          {line.replace(/\*\*/g, '')}
                        </p>
                      );
                    }
                    if (line.startsWith('- ')) {
                      return (
                        <li key={lineIdx} className="text-gray-700 ml-4">
                          {line.substring(2)}
                        </li>
                      );
                    }
                    if (line.trim() === '') {
                      return <br key={lineIdx} />;
                    }
                    return (
                      <p key={lineIdx} className="text-gray-700 mb-1">
                        {line}
                      </p>
                    );
                  })}
                </div>

                {/* Metadata Pills */}
                {interaction.metadata && Object.keys(interaction.metadata).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {interaction.metadata.word_count && (
                      <span className="px-2 py-1 bg-white rounded-full text-xs font-medium text-gray-600">
                        📝 {interaction.metadata.word_count} words
                      </span>
                    )}
                    {interaction.metadata.status && (
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          interaction.metadata.status === "approved"
                            ? "bg-green-100 text-green-700"
                            : "bg-yellow-100 text-yellow-700"
                        }`}
                      >
                        {interaction.metadata.status}
                      </span>
                    )}
                    {interaction.metadata.scene_number && (
                      <span className="px-2 py-1 bg-white rounded-full text-xs font-medium text-gray-600">
                        🎬 Scene {interaction.metadata.scene_number}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Scroll anchor */}
        <div ref={conversationEndRef} />
      </div>

      {/* Completion Message */}
      {isComplete && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-center gap-2 text-green-600">
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-lg font-semibold">Generation Complete!</span>
          </div>
        </div>
      )}
    </div>
  );
};


