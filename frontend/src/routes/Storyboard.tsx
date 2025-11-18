/**
 * Storyboard page component for viewing the storyboard plan of a video generation.
 */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getGenerationStatus } from "../lib/generationService";
import type { StatusResponse } from "../lib/generationService";
import { getGeneration } from "../lib/services/generations";
import { StoryboardVisualizer } from "../components/storyboard";
import { Button } from "../components/ui/Button";
import { ErrorMessage } from "../components/ui/ErrorMessage";

/**
 * Storyboard component displays the storyboard plan for a specific generation.
 */
export const Storyboard: React.FC = () => {
  const { generationId } = useParams<{ generationId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [prompt, setPrompt] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch generation status with storyboard plan
  useEffect(() => {
    let isMounted = true;

    const fetchStoryboard = async () => {
      if (!generationId) {
        if (isMounted) {
          setError("Generation ID is required");
          setLoading(false);
        }
        return;
      }

      try {
        if (isMounted) {
          setLoading(true);
          setError(null);
        }

        // Fetch both status (for storyboard) and generation (for prompt)
        const [statusData, generationData] = await Promise.all([
          getGenerationStatus(generationId),
          getGeneration(generationId).catch(() => null) // Don't fail if generation fetch fails
        ]);
        
        if (!isMounted) return;
        
        if (!statusData.storyboard_plan) {
          // Provide more helpful error message
          const hasImages = generationData?.thumbnail_url || statusData.video_url;
          const usedLLM = generationData?.use_llm;
          
          let errorMsg = "Storyboard not available for this generation.";
          if (usedLLM === false) {
            errorMsg += " This generation was created without LLM enhancement, so no storyboard was generated.";
          } else if (hasImages) {
            errorMsg += " The storyboard may not have been saved properly, or this generation was created before the storyboard feature was implemented.";
          } else {
            errorMsg += " It may not have been generated with LLM enhancement.";
          }
          
          setError(errorMsg);
        } else {
          setStatus(statusData);
          // Use prompt from generation data if available, otherwise use a default
          if (generationData?.prompt) {
            setPrompt(generationData.prompt);
          } else {
            setPrompt("Video generation storyboard");
          }
          
          // Debug: Log image URLs
          if (statusData.storyboard_plan?.scenes) {
            console.log("Storyboard scenes with image URLs:", statusData.storyboard_plan.scenes.map(scene => ({
              scene_number: scene.scene_number,
              reference_image_url: scene.reference_image_url,
              start_image_url: scene.start_image_url,
              end_image_url: scene.end_image_url,
            })));
          }
        }
      } catch (err) {
        if (!isMounted) return;
        
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load storyboard";
        setError(errorMessage);
        console.error("Error fetching storyboard:", err);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchStoryboard();

    return () => {
      isMounted = false;
    };
  }, [generationId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading storyboard...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <Button
              onClick={() => navigate(`/gallery/${generationId}`)}
              variant="secondary"
            >
              ← Back to Video
            </Button>
          </div>
          <ErrorMessage message={error} />
        </div>
      </div>
    );
  }

  if (!status || !status.storyboard_plan) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <Button
              onClick={() => navigate(`/gallery/${generationId}`)}
              variant="secondary"
            >
              ← Back to Video
            </Button>
          </div>
          <ErrorMessage message="Storyboard not available for this generation." />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Back button */}
        <div className="mb-6">
          <Button
            onClick={() => navigate(`/gallery/${generationId}`)}
            variant="secondary"
          >
            ← Back to Video
          </Button>
        </div>

        {/* Storyboard Visualizer */}
        {status.storyboard_plan && (
          <StoryboardVisualizer
            storyboardPlan={status.storyboard_plan}
            prompt={prompt || "Video generation storyboard"}
          />
        )}
      </div>
    </div>
  );
};

