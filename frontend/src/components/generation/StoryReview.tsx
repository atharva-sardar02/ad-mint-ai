/**
 * StoryReview Component
 *
 * Story review interface for interactive pipeline.
 * Displays generated story and allows conversational feedback before approval.
 *
 * Features:
 * - Story text display
 * - Integrated ChatInterface for feedback
 * - Approve button (proceed to next stage)
 * - Regenerate button (with feedback)
 * - Loading states
 */

import { useState } from "react";
import { ChatInterface } from "./ChatInterface";
import type { ChatMessage, StoryOutput } from "../../types/pipeline";

export interface StoryReviewProps {
  /** Generated story output */
  story: StoryOutput | null;
  /** Chat message history */
  messages: ChatMessage[];
  /** Whether story is being regenerated */
  isRegenerating?: boolean;
  /** Callback to send feedback message */
  onSendFeedback: (message: string) => void;
  /** Callback to approve story and proceed */
  onApprove: () => void;
  /** Callback to regenerate story */
  onRegenerate: () => void;
  /** Disabled state */
  disabled?: boolean;
}

export function StoryReview({
  story,
  messages,
  isRegenerating = false,
  onSendFeedback,
  onApprove,
  onRegenerate,
  disabled = false,
}: StoryReviewProps) {
  const [showFullStory, setShowFullStory] = useState(true);

  // Loading state
  if (!story) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4" />
          <p className="text-gray-600">Generating your story...</p>
        </div>
      </div>
    );
  }

  // Extract story content
  const narrativeRaw = story.narrative || "";
  const narrative =
    typeof narrativeRaw === "string"
      ? narrativeRaw
      : JSON.stringify(narrativeRaw, null, 2);
  const scriptRaw = story.script || "";
  const script =
    typeof scriptRaw === "string"
      ? scriptRaw
      : JSON.stringify(scriptRaw, null, 2);
  const storyTitle = story.story_title || "Your Story";

  return (
    <div className="flex flex-col lg:flex-row h-full gap-6">
      {/* Story Display Column */}
      <div className="flex-1 overflow-auto">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{storyTitle}</h2>
            <p className="text-sm text-gray-600 mt-1">
              Review the generated narrative before moving on
            </p>
          </div>
          <button
            onClick={() => setShowFullStory(!showFullStory)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {showFullStory ? "Collapse" : "Expand"}
          </button>
        </div>

        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 h-full">
          {showFullStory ? (
            <div className="space-y-6">
              {narrative && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    Narrative
                  </h3>
                  <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {narrative}
                  </p>
                </div>
              )}

              {script && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    Script
                  </h3>
                  <div className="text-gray-700 whitespace-pre-wrap leading-relaxed font-mono text-sm bg-gray-50 p-4 rounded border border-gray-200">
                    {script}
                  </div>
                </div>
              )}

              {story.template_id && (
                <div className="text-sm text-gray-500 border-t border-gray-200 pt-4">
                  <span className="font-medium">Template:</span>{" "}
                  {story.template_id}
                </div>
              )}

              <div className="text-sm text-gray-500 bg-blue-50 border border-blue-200 rounded p-3">
                <p className="font-medium text-blue-900 mb-1">Tips</p>
                <ul className="list-disc list-inside space-y-1 text-blue-800">
                  <li>Chat with the AI to refine the story before approving.</li>
                  <li>
                    Be specific: “Make it more humorous” or “Focus on product
                    benefits.”
                  </li>
                  <li>Use Regenerate to apply the latest feedback.</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              Story collapsed. Click “Expand” to view.
            </div>
          )}
        </div>
      </div>

      {/* Chat & Actions Column */}
      <div className="lg:w-96 flex flex-col">
        <div className="flex-1 bg-white rounded-lg shadow-md overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Feedback</h3>
            <p className="text-sm text-gray-600 mt-1">
              Describe what you’d like to change
            </p>
          </div>

          <ChatInterface
            messages={messages}
            onSendMessage={onSendFeedback}
            isProcessing={isRegenerating}
            placeholder="Type your feedback... (e.g., 'Make it more humorous')"
            disabled={disabled || isRegenerating}
          />
        </div>

        <div className="mt-4 space-y-3">
          <button
            onClick={onRegenerate}
            disabled={disabled || isRegenerating}
            className="w-full px-6 py-3 bg-yellow-500 text-white font-semibold rounded-lg hover:bg-yellow-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isRegenerating ? "Regenerating..." : "Regenerate"}
          </button>

          <button
            onClick={onApprove}
            disabled={disabled || isRegenerating}
            className="w-full px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            ✓ Approve &amp; Continue
          </button>
        </div>
      </div>
    </div>
  );
}
