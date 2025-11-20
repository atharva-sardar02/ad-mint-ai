/**
 * Storyboard Visualizer component for displaying the storyboard plan with images and story details.
 */
import React, { useState } from "react";
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
  const { consistency_markers, scenes, llm_input, llm_output } = storyboardPlan;
  const [selectedImage, setSelectedImage] = useState<{ url: string; alt: string } | null>(null);

  return (
    <>
      {/* Image Modal/Popup */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-7xl max-h-full">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 z-10 text-white bg-black bg-opacity-50 hover:bg-opacity-75 rounded-full p-2 transition-all"
              aria-label="Close"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
            <img
              src={selectedImage.url}
              alt={selectedImage.alt}
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}

      <div className="storyboard-visualizer bg-white rounded-lg shadow-md p-6 my-4">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Storyboard</h2>
      
      {/* Complete Flow: User Prompt → LLM → Images → Videos */}
      <div className="mb-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Complete Generation Flow</h3>
        
        {/* Step 1: User Prompt */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-500 text-white text-xs font-bold">1</span>
            <h3 className="text-sm font-semibold text-blue-900">User Prompt</h3>
          </div>
          <p className="text-gray-700 ml-8">{prompt}</p>
        </div>

        {/* Step 2: LLM Input */}
        {llm_input && (
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2 mb-3">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-green-500 text-white text-xs font-bold">2</span>
              <h3 className="text-sm font-semibold text-green-900">LLM Input (Storyboard Planning)</h3>
            </div>
            <div className="ml-8 space-y-3">
              <div>
                <p className="text-xs font-medium text-green-700 mb-1">Model: {llm_input.model || "gpt-4o"}</p>
                <p className="text-xs font-medium text-green-700 mb-1">Number of Scenes: {llm_input.num_scenes || scenes.length}</p>
                {llm_input.reference_image_provided && (
                  <p className="text-xs font-medium text-green-700 mb-1">Reference Image: Provided</p>
                )}
              </div>
              {llm_input.system_prompt && (
                <details className="mt-2">
                  <summary className="text-xs font-medium text-green-700 cursor-pointer hover:text-green-900">
                    System Prompt (Click to expand)
                  </summary>
                  <div className="mt-2 p-3 bg-white rounded border border-green-200">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">{llm_input.system_prompt}</pre>
                  </div>
                </details>
              )}
              {llm_input.user_message && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-green-700 mb-1">User Message:</p>
                  <div className="p-3 bg-white rounded border border-green-200">
                    <p className="text-xs text-gray-700">{llm_input.user_message}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 3: LLM Output */}
        {llm_output && (
          <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex items-center gap-2 mb-3">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-500 text-white text-xs font-bold">3</span>
              <h3 className="text-sm font-semibold text-purple-900">LLM Output (Storyboard Plan)</h3>
            </div>
            <div className="ml-8 space-y-2">
              <p className="text-xs font-medium text-purple-700">Model Used: {llm_output.model_used || "gpt-4o"}</p>
              <p className="text-xs font-medium text-purple-700">Finish Reason: {llm_output.finish_reason || "stop"}</p>
              {llm_output.raw_response && (
                <details className="mt-2">
                  <summary className="text-xs font-medium text-purple-700 cursor-pointer hover:text-purple-900">
                    Raw LLM Response (JSON) - Click to expand
                  </summary>
                  <div className="mt-2 p-3 bg-white rounded border border-purple-200 max-h-96 overflow-auto">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">{llm_output.raw_response}</pre>
                  </div>
                </details>
              )}
            </div>
          </div>
        )}
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
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <h5 className="text-xs font-semibold text-gray-600 mb-2">Reference Image</h5>
                {scene.reference_image_url ? (
                  <>
                    <div 
                      className="relative w-full min-h-48 bg-gray-50 rounded-lg mb-2 overflow-hidden cursor-pointer hover:shadow-lg transition-all border border-gray-200 flex items-center justify-center"
                      onClick={() => setSelectedImage({ url: scene.reference_image_url!, alt: `Scene ${scene.scene_number} - Reference` })}
                    >
                      <img
                        src={scene.reference_image_url}
                        alt={`Scene ${scene.scene_number} - Reference`}
                        className="w-full h-auto max-h-64 object-contain rounded-lg"
                        onError={(e) => {
                          console.error(`Failed to load reference image for scene ${scene.scene_number}:`, scene.reference_image_url);
                          (e.target as HTMLImageElement).src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23ddd' width='200' height='200'/%3E%3Ctext fill='%23999' font-family='sans-serif' font-size='14' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EImage Loading...%3C/text%3E%3C/svg%3E";
                        }}
                        onLoad={(e) => {
                          console.log(`Successfully loaded reference image for scene ${scene.scene_number}:`, scene.reference_image_url);
                          // Ensure image is visible
                          (e.target as HTMLImageElement).style.display = 'block';
                        }}
                        style={{ display: 'block' }}
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-20 transition-all pointer-events-none">
                        <div className="opacity-0 hover:opacity-100 transition-opacity">
                          <svg className="w-12 h-12 text-white drop-shadow-lg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                          </svg>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 text-center mb-2">Click to view full size</p>
                    {(scene.reference_image_prompt || scene.detailed_prompt) && (
                      <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-100">
                        <p className="text-xs font-medium text-gray-700 mb-1">Image Prompt:</p>
                        <p className="text-xs text-gray-600 leading-relaxed">
                          {scene.reference_image_prompt || scene.detailed_prompt}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="w-full h-48 bg-gray-100 rounded-lg mb-2 flex items-center justify-center border-2 border-dashed border-gray-300">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                      <p className="text-xs text-gray-500">Generating reference image...</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Start Image (for Kling 2.5 Turbo Pro) */}
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <h5 className="text-xs font-semibold text-gray-600 mb-2">Start Frame</h5>
                {scene.start_image_url ? (
                  <>
                    <div 
                      className="relative w-full min-h-48 bg-gray-50 rounded-lg mb-2 overflow-hidden cursor-pointer hover:shadow-lg transition-all border border-gray-200 flex items-center justify-center"
                      onClick={() => setSelectedImage({ url: scene.start_image_url!, alt: `Scene ${scene.scene_number} - Start` })}
                    >
                      <img
                        src={scene.start_image_url}
                        alt={`Scene ${scene.scene_number} - Start`}
                        className="w-full h-auto max-h-64 object-contain rounded-lg"
                        onError={(e) => {
                          console.error(`Failed to load start image for scene ${scene.scene_number}:`, scene.start_image_url);
                          (e.target as HTMLImageElement).src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23ddd' width='200' height='200'/%3E%3Ctext fill='%23999' font-family='sans-serif' font-size='14' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EImage Loading...%3C/text%3E%3C/svg%3E";
                        }}
                        onLoad={(e) => {
                          console.log(`Successfully loaded start image for scene ${scene.scene_number}:`, scene.start_image_url);
                          // Ensure image is visible
                          (e.target as HTMLImageElement).style.display = 'block';
                        }}
                        style={{ display: 'block' }}
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-20 transition-all pointer-events-none">
                        <div className="opacity-0 hover:opacity-100 transition-opacity">
                          <svg className="w-12 h-12 text-white drop-shadow-lg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                          </svg>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 text-center mb-2">Click to view full size</p>
                    {(scene.start_image_enhanced_prompt || scene.start_image_prompt) && (
                      <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-100">
                        <p className="text-xs font-medium text-gray-700 mb-1">Image Prompt:</p>
                        <p className="text-xs text-gray-600 leading-relaxed">
                          {scene.start_image_enhanced_prompt || scene.start_image_prompt}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="w-full h-48 bg-gray-100 rounded-lg mb-2 flex items-center justify-center border-2 border-dashed border-gray-300">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                      <p className="text-xs text-gray-500">Generating start frame...</p>
                    </div>
                  </div>
                )}
              </div>

              {/* End Image (for Kling 2.5 Turbo Pro) */}
              <div className="bg-white rounded-lg p-3 border border-gray-200">
                <h5 className="text-xs font-semibold text-gray-600 mb-2">End Frame</h5>
                {scene.end_image_url ? (
                  <>
                    <div 
                      className="relative w-full min-h-48 bg-gray-50 rounded-lg mb-2 overflow-hidden cursor-pointer hover:shadow-lg transition-all border border-gray-200 flex items-center justify-center"
                      onClick={() => setSelectedImage({ url: scene.end_image_url!, alt: `Scene ${scene.scene_number} - End` })}
                    >
                      <img
                        src={scene.end_image_url}
                        alt={`Scene ${scene.scene_number} - End`}
                        className="w-full h-auto max-h-64 object-contain rounded-lg"
                        onError={(e) => {
                          console.error(`Failed to load end image for scene ${scene.scene_number}:`, scene.end_image_url);
                          (e.target as HTMLImageElement).src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23ddd' width='200' height='200'/%3E%3Ctext fill='%23999' font-family='sans-serif' font-size='14' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EImage Loading...%3C/text%3E%3C/svg%3E";
                        }}
                        onLoad={(e) => {
                          console.log(`Successfully loaded end image for scene ${scene.scene_number}:`, scene.end_image_url);
                          // Ensure image is visible
                          (e.target as HTMLImageElement).style.display = 'block';
                        }}
                        style={{ display: 'block' }}
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-20 transition-all pointer-events-none">
                        <div className="opacity-0 hover:opacity-100 transition-opacity">
                          <svg className="w-12 h-12 text-white drop-shadow-lg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                          </svg>
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 text-center mb-2">Click to view full size</p>
                    {(scene.end_image_enhanced_prompt || scene.end_image_prompt) && (
                      <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-100">
                        <p className="text-xs font-medium text-gray-700 mb-1">Image Prompt:</p>
                        <p className="text-xs text-gray-600 leading-relaxed">
                          {scene.end_image_enhanced_prompt || scene.end_image_prompt}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="w-full h-48 bg-gray-100 rounded-lg mb-2 flex items-center justify-center border-2 border-dashed border-gray-300">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                      <p className="text-xs text-gray-500">Generating end frame...</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Scene Description - Complete Flow */}
            <div className="space-y-4">
              {/* Step 4: Image Generation Prompts */}
              <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="flex items-center gap-2 mb-3">
                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-yellow-500 text-white text-xs font-bold">4</span>
                  <h5 className="text-sm font-semibold text-yellow-900">Image Generation Prompts</h5>
                </div>
                <div className="ml-8 space-y-3">
                  {scene.image_generation_prompt ? (
                    <div>
                      <p className="text-xs font-medium text-yellow-700 mb-1">Base Image Generation Prompt:</p>
                      <p className="text-sm text-gray-700 leading-relaxed">{scene.image_generation_prompt}</p>
                    </div>
                  ) : scene.detailed_prompt ? (
                    <div>
                      <p className="text-xs font-medium text-yellow-700 mb-1">Base Prompt (from LLM):</p>
                      <p className="text-sm text-gray-700 leading-relaxed italic">{scene.detailed_prompt}</p>
                      <p className="text-xs text-yellow-600 mt-1">Note: Detailed image generation prompt not available, showing base prompt.</p>
                    </div>
                  ) : (
                    <p className="text-xs text-yellow-600 italic">Image generation prompt not available for this scene.</p>
                  )}
                  
                  {scene.reference_image_prompt ? (
                    <div className="p-2 bg-white rounded border border-yellow-200">
                      <p className="text-xs font-medium text-yellow-700 mb-1">Enhanced Reference Image Prompt (with markers):</p>
                      <p className="text-xs text-gray-600 leading-relaxed">{scene.reference_image_prompt}</p>
                    </div>
                  ) : scene.reference_image_url && (
                    <div className="p-2 bg-yellow-100 rounded border border-yellow-300">
                      <p className="text-xs text-yellow-700 italic">Enhanced reference image prompt not stored. Image was generated but prompt details are missing.</p>
                    </div>
                  )}
                  
                  {scene.start_image_enhanced_prompt ? (
                    <div className="p-2 bg-white rounded border border-yellow-200">
                      <p className="text-xs font-medium text-yellow-700 mb-1">Enhanced Start Image Prompt (with markers):</p>
                      <p className="text-xs text-gray-600 leading-relaxed">{scene.start_image_enhanced_prompt}</p>
                    </div>
                  ) : scene.start_image_prompt && (
                    <div className="p-2 bg-white rounded border border-yellow-200">
                      <p className="text-xs font-medium text-yellow-700 mb-1">Base Start Image Prompt:</p>
                      <p className="text-xs text-gray-600 leading-relaxed">{scene.start_image_prompt}</p>
                      <p className="text-xs text-yellow-600 mt-1 italic">Enhanced prompt with markers not available.</p>
                    </div>
                  )}
                  
                  {scene.end_image_enhanced_prompt ? (
                    <div className="p-2 bg-white rounded border border-yellow-200">
                      <p className="text-xs font-medium text-yellow-700 mb-1">Enhanced End Image Prompt (with markers):</p>
                      <p className="text-xs text-gray-600 leading-relaxed">{scene.end_image_enhanced_prompt}</p>
                    </div>
                  ) : scene.end_image_prompt && (
                    <div className="p-2 bg-white rounded border border-yellow-200">
                      <p className="text-xs font-medium text-yellow-700 mb-1">Base End Image Prompt:</p>
                      <p className="text-xs text-gray-600 leading-relaxed">{scene.end_image_prompt}</p>
                      <p className="text-xs text-yellow-600 mt-1 italic">Enhanced prompt with markers not available.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Step 5: Video Generation Prompts */}
              <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-center gap-2 mb-3">
                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-red-500 text-white text-xs font-bold">5</span>
                  <h5 className="text-sm font-semibold text-red-900">Video Generation Prompt</h5>
                  {scene.video_generation_model && (
                    <span className="text-xs text-red-700 bg-red-100 px-2 py-1 rounded">Model: {scene.video_generation_model}</span>
                  )}
                </div>
                <div className="ml-8 space-y-2">
                  {scene.video_generation_base_prompt && (
                    <div>
                      <p className="text-xs font-medium text-red-700 mb-1">Base Prompt (from LLM):</p>
                      <p className="text-sm text-gray-700 leading-relaxed">{scene.video_generation_base_prompt}</p>
                    </div>
                  )}
                  {scene.video_generation_prompt && (
                    <div className="p-2 bg-white rounded border border-red-200">
                      <p className="text-xs font-medium text-red-700 mb-1">Enhanced Prompt (with consistency markers):</p>
                      <p className="text-sm text-gray-700 leading-relaxed font-medium">{scene.video_generation_prompt}</p>
                      <p className="text-xs text-red-600 mt-2 italic">
                        This is the actual prompt sent to the video generation model ({scene.video_generation_model || "Kling 2.5 Turbo Pro (default)"}).
                      </p>
                    </div>
                  )}
                  {!scene.video_generation_prompt && scene.detailed_prompt && (
                    <div>
                      <p className="text-xs font-medium text-red-700 mb-1">Base Prompt (from LLM):</p>
                      <p className="text-sm text-gray-700 leading-relaxed">{scene.detailed_prompt}</p>
                      {consistency_markers && (
                        <div className="mt-2 p-2 bg-red-100 rounded border border-red-300">
                          <p className="text-xs font-medium text-red-700 mb-1">Consistency Markers (would be added):</p>
                          <div className="text-xs text-red-600 space-y-1">
                            {consistency_markers.style && <p>• Style: {consistency_markers.style}</p>}
                            {consistency_markers.color_palette && <p>• Color Palette: {consistency_markers.color_palette}</p>}
                            {consistency_markers.lighting && <p>• Lighting: {consistency_markers.lighting}</p>}
                            {consistency_markers.composition && <p>• Composition: {consistency_markers.composition}</p>}
                            {consistency_markers.mood && <p>• Mood: {consistency_markers.mood}</p>}
                          </div>
                          <p className="text-xs text-red-600 mt-2 italic">
                            Enhanced prompt not stored. This is what would be sent to the video model.
                          </p>
                        </div>
                      )}
                      {!consistency_markers && (
                        <p className="text-xs text-red-600 mt-2 italic">
                          Video generation prompt will be enhanced with consistency markers before sending to model.
                        </p>
                      )}
                    </div>
                  )}
                  {!scene.video_generation_prompt && !scene.detailed_prompt && (
                    <p className="text-xs text-red-600 italic">Video generation prompt not available for this scene.</p>
                  )}
                </div>
              </div>

              {/* Additional Scene Details */}
              {scene.image_continuity_notes && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <h5 className="text-sm font-semibold text-green-900 mb-2">Continuity Notes</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">{scene.image_continuity_notes}</p>
                </div>
              )}

              {scene.visual_consistency_guidelines && (
                <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                  <h5 className="text-sm font-semibold text-indigo-900 mb-2">Visual Consistency Guidelines</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">{scene.visual_consistency_guidelines}</p>
                </div>
              )}

              {/* Detailed Image Generation Prompt */}
              {scene.image_generation_prompt && (
                <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <h5 className="text-sm font-semibold text-yellow-900 mb-2">Detailed Image Generation Prompt</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">{scene.image_generation_prompt}</p>
                  <p className="text-xs text-yellow-700 mt-2 italic">
                    This detailed prompt is specifically crafted for image generation to ensure maximum visual consistency.
                  </p>
                </div>
              )}

              {/* Continuity Notes */}
              {scene.image_continuity_notes && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <h5 className="text-sm font-semibold text-green-900 mb-2">Continuity Notes</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">{scene.image_continuity_notes}</p>
                  <p className="text-xs text-green-700 mt-2 italic">
                    How this scene visually relates to previous scenes to maintain consistency.
                  </p>
                </div>
              )}

              {/* Visual Consistency Guidelines */}
              {scene.visual_consistency_guidelines && (
                <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                  <h5 className="text-sm font-semibold text-indigo-900 mb-2">Visual Consistency Guidelines</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">{scene.visual_consistency_guidelines}</p>
                  <p className="text-xs text-indigo-700 mt-2 italic">
                    Per-scene specific instructions for maintaining visual consistency.
                  </p>
                </div>
              )}

              {/* Scene Transition Notes */}
              {scene.scene_transition_notes && (
                <div className="p-3 bg-pink-50 rounded-lg border border-pink-200">
                  <h5 className="text-sm font-semibold text-pink-900 mb-2">Scene Transition Notes</h5>
                  <p className="text-sm text-gray-700 leading-relaxed">{scene.scene_transition_notes}</p>
                  <p className="text-xs text-pink-700 mt-2 italic">
                    How this scene visually transitions from the previous scene.
                  </p>
                </div>
              )}

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
    </>
  );
};

