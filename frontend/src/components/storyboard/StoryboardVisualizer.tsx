/**
 * Storyboard Visualizer component for displaying the storyboard plan with images and story details.
 */
import React from "react";
import type { StoryboardPlan } from "../../lib/generationService";

interface StoryboardVisualizerProps {
  storyboardPlan: StoryboardPlan;
  prompt: string;
}

/**
 * StoryboardVisualizer displays the storyboard plan with:
 * - Consistency markers (style, color, lighting, etc.)
 * - Each scene with its images (reference, start, end) and story details
 * - AIDA stage information
 */
export const StoryboardVisualizer: React.FC<StoryboardVisualizerProps> = ({
  storyboardPlan,
  prompt,
}) => {
  const { consistency_markers, scenes } = storyboardPlan;

  return (
    <div className="storyboard-visualizer bg-white rounded-lg shadow-md p-6 my-4">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Storyboard</h2>
      
      {/* Original Prompt */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">Original Prompt</h3>
        <p className="text-gray-700">{prompt}</p>
      </div>

      {/* Consistency Markers */}
      {consistency_markers && (
        <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <h3 className="text-sm font-semibold text-purple-900 mb-3">Visual Consistency</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {consistency_markers.style && (
              <div>
                <span className="text-xs font-medium text-purple-700">Style:</span>
                <p className="text-sm text-gray-700">{consistency_markers.style}</p>
              </div>
            )}
            {consistency_markers.color_palette && (
              <div>
                <span className="text-xs font-medium text-purple-700">Color Palette:</span>
                <p className="text-sm text-gray-700">{consistency_markers.color_palette}</p>
              </div>
            )}
            {consistency_markers.lighting && (
              <div>
                <span className="text-xs font-medium text-purple-700">Lighting:</span>
                <p className="text-sm text-gray-700">{consistency_markers.lighting}</p>
              </div>
            )}
            {consistency_markers.composition && (
              <div>
                <span className="text-xs font-medium text-purple-700">Composition:</span>
                <p className="text-sm text-gray-700">{consistency_markers.composition}</p>
              </div>
            )}
            {consistency_markers.mood && (
              <div>
                <span className="text-xs font-medium text-purple-700">Mood:</span>
                <p className="text-sm text-gray-700">{consistency_markers.mood}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scenes */}
      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Scenes</h3>
        {scenes.map((scene, index) => (
          <div
            key={scene.scene_number}
            className="border border-gray-200 rounded-lg p-5 bg-gray-50 hover:shadow-md transition-shadow"
          >
            {/* Scene Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-500 text-white font-bold">
                  {scene.scene_number}
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-gray-800">
                    Scene {scene.scene_number}: {scene.aida_stage}
                  </h4>
                  <p className="text-sm text-gray-500">
                    Duration: {scene.duration_seconds}s
                  </p>
                </div>
              </div>
            </div>

            {/* Scene Images */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {/* Reference Image */}
              {scene.reference_image_url && (
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <h5 className="text-xs font-semibold text-gray-600 mb-2">Reference Image</h5>
                  <img
                    src={scene.reference_image_url}
                    alt={`Scene ${scene.scene_number} - Reference`}
                    className="w-full h-48 object-cover rounded-lg mb-2"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23ddd' width='200' height='200'/%3E%3Ctext fill='%23999' font-family='sans-serif' font-size='14' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EImage Loading...%3C/text%3E%3C/svg%3E";
                    }}
                  />
                  {(scene.reference_image_prompt || scene.detailed_prompt) && (
                    <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-100">
                      <p className="text-xs font-medium text-gray-700 mb-1">Image Prompt:</p>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        {scene.reference_image_prompt || scene.detailed_prompt}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Start Image (for Kling 2.5 Turbo Pro) */}
              {scene.start_image_url && (
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <h5 className="text-xs font-semibold text-gray-600 mb-2">Start Frame</h5>
                  <img
                    src={scene.start_image_url}
                    alt={`Scene ${scene.scene_number} - Start`}
                    className="w-full h-48 object-cover rounded-lg mb-2"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23ddd' width='200' height='200'/%3E%3Ctext fill='%23999' font-family='sans-serif' font-size='14' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EImage Loading...%3C/text%3E%3C/svg%3E";
                    }}
                  />
                  {(scene.start_image_enhanced_prompt || scene.start_image_prompt) && (
                    <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-100">
                      <p className="text-xs font-medium text-gray-700 mb-1">Image Prompt:</p>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        {scene.start_image_enhanced_prompt || scene.start_image_prompt}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* End Image (for Kling 2.5 Turbo Pro) */}
              {scene.end_image_url && (
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <h5 className="text-xs font-semibold text-gray-600 mb-2">End Frame</h5>
                  <img
                    src={scene.end_image_url}
                    alt={`Scene ${scene.scene_number} - End`}
                    className="w-full h-48 object-cover rounded-lg mb-2"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23ddd' width='200' height='200'/%3E%3Ctext fill='%23999' font-family='sans-serif' font-size='14' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EImage Loading...%3C/text%3E%3C/svg%3E";
                    }}
                  />
                  {(scene.end_image_enhanced_prompt || scene.end_image_prompt) && (
                    <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-100">
                      <p className="text-xs font-medium text-gray-700 mb-1">Image Prompt:</p>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        {scene.end_image_enhanced_prompt || scene.end_image_prompt}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Scene Description */}
            <div className="space-y-3">
              <div>
                <h5 className="text-sm font-semibold text-gray-700 mb-2">Story</h5>
                <p className="text-sm text-gray-600 leading-relaxed">{scene.detailed_prompt}</p>
              </div>

              {/* Scene Details */}
              {scene.scene_description && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  {scene.scene_description.environment && (
                    <div>
                      <span className="font-medium text-gray-700">Environment: </span>
                      <span className="text-gray-600">{scene.scene_description.environment}</span>
                    </div>
                  )}
                  {scene.scene_description.character_action && (
                    <div>
                      <span className="font-medium text-gray-700">Action: </span>
                      <span className="text-gray-600">{scene.scene_description.character_action}</span>
                    </div>
                  )}
                  {scene.scene_description.camera_angle && (
                    <div>
                      <span className="font-medium text-gray-700">Camera: </span>
                      <span className="text-gray-600">{scene.scene_description.camera_angle}</span>
                    </div>
                  )}
                  {scene.scene_description.composition && (
                    <div>
                      <span className="font-medium text-gray-700">Composition: </span>
                      <span className="text-gray-600">{scene.scene_description.composition}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

