/**
 * ImageReview Component
 *
 * Gallery display for reference images or storyboard images with review capabilities.
 * Supports image selection, conversational feedback, and approval flow.
 *
 * Features:
 * - Responsive grid layout (1-3 columns)
 * - Image selection (single and multi-select)
 * - Quality score badges
 * - Click-to-enlarge modal
 * - Integrated chat interface
 * - Approve/Regenerate actions
 */

import React, { useEffect, useState } from "react";
import { ChatInterface } from "./ChatInterface";
import ImageEditor from "./ImageEditor";
import type { ChatMessage } from "../../types/pipeline";
import { getAssetUrl } from "../../utils/url";
import { formatDuration } from "../../utils/time";

export interface ImageData {
  index: number;
  path: string;
  url: string;
  prompt?: string;
  quality_score?: number | null;
  quality_metrics?: Record<string, number | null>;
  is_edited?: boolean; // Story 4: Track if image has been edited
  edit_version?: number; // Story 4: Current edit version
}

export interface StoryboardClip {
  clip_number: number;
  start_frame: {
    path: string;
    url: string;
  };
  end_frame: {
    path: string;
    url: string;
  };
  duration: number;
  description: string;
  prompt: string;
  voiceover?: string;
  scene?: any;
  quality_score?: number | null;
  quality_metrics?: Record<string, number | null>;
}

export interface ImageReviewProps {
  /** Stage type: reference_image or storyboard */
  stage: "reference_image" | "storyboard";
  /** List of images (for reference_image) or clips (for storyboard) */
  images?: ImageData[];
  clips?: StoryboardClip[];
  /** Conversation messages */
  messages: ChatMessage[];
  /** Whether regeneration is in progress */
  isRegenerating?: boolean;
  /** Callback to send feedback */
  onSendFeedback: (message: string, selectedIndices?: number[]) => void;
  /** Callback to approve stage */
  onApprove: () => void;
  /** Callback to regenerate with feedback */
  onRegenerate: (selectedIndices?: number[]) => void;
  /** Whether actions are disabled */
  disabled?: boolean;
  /** Session ID (Story 4: Required for image editing) */
  sessionId?: string;
  /** Callback when image is edited (Story 4: Update image in gallery) */
  onImageEdited?: (imageIndex: number, editedUrl: string, version: number) => void;
  /** Callback when selection changes */
  onSelectionChange?: (selectedIndices: number[]) => void;
  /** Initial selection to seed UI */
  initialSelection?: number[];
  /** Stage duration in seconds */
  durationSeconds?: number;
}

export function ImageReview({
  stage,
  images = [],
  clips = [],
  messages,
  isRegenerating = false,
  onSendFeedback,
  onApprove,
  onRegenerate,
  disabled = false,
  sessionId,
  onImageEdited,
  onSelectionChange,
  initialSelection,
  durationSeconds,
}: ImageReviewProps) {
  const getDefaultSelection = () => {
    if (initialSelection && initialSelection.length > 0) {
      return new Set(initialSelection);
    }
    if (stage === "reference_image" && images.length > 0) {
      return new Set([images[0].index]);
    }
    return new Set<number>();
  };

  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(getDefaultSelection());
  const [enlargedImage, setEnlargedImage] = useState<string | null>(null);

  // Story 4: Image editing state
  const [editingImage, setEditingImage] = useState<{
    index: number;
    url: string;
  } | null>(null);

  const isStoryboard = stage === "storyboard";
  const itemCount = isStoryboard ? clips.length : images.length;

  // Handle image selection
  const handleImageClick = (index: number) => {
    const newSelected = new Set(selectedIndices);
    if (isStoryboard) {
      if (newSelected.has(index)) {
        newSelected.delete(index);
      } else {
        newSelected.add(index);
      }
    } else {
      newSelected.clear();
      newSelected.add(index);
    }
    setSelectedIndices(newSelected);
    onSelectionChange?.(Array.from(newSelected));
  };

  useEffect(() => {
    const defaults = getDefaultSelection();

    // Compare with current selection to avoid infinite update loops
    const isDifferent =
      defaults.size !== selectedIndices.size ||
      Array.from(defaults).some((value) => !selectedIndices.has(value));

    if (!isDifferent) {
      return;
    }

    setSelectedIndices(defaults);
    onSelectionChange?.(Array.from(defaults));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [images, initialSelection, stage]);

  // Handle enlarge (with Shift+Click or dedicated button)
  const handleEnlarge = (url: string, event?: React.MouseEvent) => {
    if (event) event.stopPropagation();
    setEnlargedImage(url);
  };

  // Handle send feedback with selected images
  const handleSendFeedback = (message: string) => {
    const selectedArray = Array.from(selectedIndices);
    onSendFeedback(message, selectedArray.length > 0 ? selectedArray : undefined);
  };

  // Handle regenerate with selected images
  const handleRegenerate = () => {
    const selectedArray = Array.from(selectedIndices);
    onRegenerate(selectedArray.length > 0 ? selectedArray : undefined);
    if (stage === "reference_image" && images.length > 0) {
      const fallbackSelection = selectedArray.length > 0 ? selectedArray : [images[0].index];
      setSelectedIndices(new Set(fallbackSelection));
      onSelectionChange?.(fallbackSelection);
    }
  };

  // Story 4: Handle edit button click
  const handleEditClick = (index: number, url: string, event?: React.MouseEvent) => {
    if (event) event.stopPropagation();
    setEditingImage({ index, url });
  };

  // Story 4: Handle save edited image
  const handleSaveEdited = (editedUrl: string, version: number, _editHistory: string[]) => {
    if (editingImage && onImageEdited) {
      onImageEdited(editingImage.index, editedUrl, version);
    }
    setEditingImage(null);
  };

  // Story 4: Handle cancel editing
  const handleCancelEdit = () => {
    setEditingImage(null);
  };

  const renderQualityDetails = (metrics?: Record<string, number | null>) => {
    if (!metrics) return null;
    const entries = Object.entries(metrics).filter(
      ([, value]) => value !== undefined && value !== null
    );
    if (!entries.length) return null;

    return (
      <div className="mt-3 bg-white/90 rounded border border-gray-100 p-2 text-xs text-gray-600">
        <p className="font-semibold text-gray-800 mb-1">Quality Metrics</p>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1">
          {entries.map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <dt className="capitalize">{key.replace(/_/g, " ")}</dt>
              <dd className="font-semibold">
                {typeof value === "number" ? value.toFixed(1) : value}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    );
  };

  // Render quality score badge
  const renderQualityScore = (score: number | null | undefined) => {
    if (!score) return null;

    const color =
      score >= 80
        ? "bg-green-100 text-green-800"
        : score >= 60
        ? "bg-yellow-100 text-yellow-800"
        : "bg-red-100 text-red-800";

    return (
      <span
        className={`absolute top-2 left-2 px-2 py-1 rounded text-xs font-semibold ${color}`}
      >
        {score}/100
      </span>
    );
  };

  // Render reference image card
  const renderImageCard = (image: ImageData) => {
    const isSelected = selectedIndices.has(image.index);

    return (
      <div
        key={image.index}
        className={`relative group cursor-pointer rounded-lg overflow-hidden shadow-md hover:shadow-xl transition-all ${
          isSelected ? "ring-4 ring-blue-500" : ""
        }`}
        onClick={() => handleImageClick(image.index)}
      >
        {/* Quality Score */}
        {renderQualityScore(image.quality_score)}

        {/* Story 4: Edited Badge */}
        {image.is_edited && (
          <span className="absolute top-2 left-20 px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-semibold">
            Edited v{image.edit_version || 1}
          </span>
        )}

        {/* Image */}
        <div className="aspect-video bg-gray-100">
          <img
            src={getAssetUrl(image.url)}
            alt={`Image ${image.index}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src =
                "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect fill='%23ddd' width='100' height='100'/%3E%3Ctext fill='%23999' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EError%3C/text%3E%3C/svg%3E";
            }}
          />
        </div>

        {/* Overlay with actions */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity flex items-center justify-center gap-2">
          <button
            onClick={(e) => handleEnlarge(getAssetUrl(image.url), e)}
            className="opacity-0 group-hover:opacity-100 px-4 py-2 bg-white text-gray-900 rounded-lg text-sm font-semibold hover:bg-gray-100 transition-opacity"
          >
            View Full Size
          </button>
          {/* Story 4: Edit Button */}
          {sessionId && (
            <button
              onClick={(e) => handleEditClick(image.index, image.url, e)}
              className="opacity-0 group-hover:opacity-100 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-opacity"
            >
              Edit
            </button>
          )}
        </div>

        {/* Selection indicator */}
        {isSelected && (
          <div className="absolute top-2 right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
            ✓
          </div>
        )}

        {/* Image number */}
        <div className="absolute bottom-2 right-2 px-2 py-1 bg-gray-900 bg-opacity-75 text-white text-xs rounded">
          Image {image.index}
        </div>

        {renderQualityDetails(image.quality_metrics)}
      </div>
    );
  };

  // Render storyboard clip card
  const renderClipCard = (clip: StoryboardClip) => {
    const isSelected = selectedIndices.has(clip.clip_number);

    return (
      <div
        key={clip.clip_number}
        className={`relative group cursor-pointer rounded-lg overflow-hidden shadow-md hover:shadow-xl transition-all ${
          isSelected ? "ring-4 ring-blue-500" : ""
        }`}
        onClick={() => handleImageClick(clip.clip_number)}
      >
        {/* Quality Score */}
        {renderQualityScore(clip.quality_score)}

        {/* Clip frames (start and end) */}
        <div className="grid grid-cols-2 gap-1">
          <div className="aspect-video bg-gray-100 relative">
            <img
              src={getAssetUrl(clip.start_frame.url)}
              alt={`Clip ${clip.clip_number} start`}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-1 left-1 px-1 py-0.5 bg-black bg-opacity-75 text-white text-xs rounded">
              Start
            </div>
          </div>
          <div className="aspect-video bg-gray-100 relative">
            <img
              src={getAssetUrl(clip.end_frame.url)}
              alt={`Clip ${clip.clip_number} end`}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-1 right-1 px-1 py-0.5 bg-black bg-opacity-75 text-white text-xs rounded">
              End
            </div>
          </div>
        </div>

        {/* Clip info */}
        <div className="p-3 bg-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-900">
              Clip {clip.clip_number}
            </span>
            <span className="text-xs text-gray-500">{clip.duration}s</span>
          </div>
          {clip.voiceover && (
            <p className="text-xs text-gray-600 line-clamp-2">
              {clip.voiceover}
            </p>
          )}
          {renderQualityDetails(clip.quality_metrics)}
        </div>

        {/* Selection indicator */}
        {isSelected && (
          <div className="absolute top-2 right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
            ✓
          </div>
        )}

        {/* Enlarge button */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity flex items-center justify-center">
          <button
            onClick={(e) => handleEnlarge(getAssetUrl(clip.start_frame.url), e)}
            className="opacity-0 group-hover:opacity-100 px-4 py-2 bg-white text-gray-900 rounded-lg text-sm font-semibold hover:bg-gray-100 transition-opacity"
          >
            View Full Size
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col lg:flex-row h-full gap-6">
      {/* Gallery Section */}
      <div className="flex-1 overflow-auto">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {isStoryboard ? "Storyboard Clips" : "Reference Images"}
          </h2>
          <p className="text-sm text-gray-600">
            {selectedIndices.size > 0
              ? `${selectedIndices.size} selected • Click to select/deselect images for targeted feedback`
              : "Click images to select for targeted feedback, or provide general feedback for all"}
          </p>
          {durationSeconds && (
            <p className="text-xs text-gray-500 mt-1">
              Stage completed in {formatDuration(durationSeconds)}
            </p>
          )}
          {stage === "reference_image" && (
            <p className="text-xs text-gray-500 mt-1">
              {selectedIndices.size > 0
                ? `Selected image: Image ${Array.from(selectedIndices).join(", ")}`
                : "Select one image to carry forward to the storyboard stage."}
            </p>
          )}
        </div>

        {/* Gallery Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {isStoryboard
            ? clips.map((clip) => renderClipCard(clip))
            : images.map((image) => renderImageCard(image))}
        </div>

        {/* Empty state */}
        {itemCount === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">
              {isRegenerating
                ? "Generating images..."
                : "No images available"}
            </p>
            {isRegenerating && (
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mt-4" />
            )}
          </div>
        )}

        {/* Selection actions */}
        {selectedIndices.size > 0 && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-900">
                {selectedIndices.size}{" "}
                {isStoryboard ? "clip(s)" : "image(s)"} selected
              </span>
              <button
                onClick={() => setSelectedIndices(new Set())}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Clear Selection
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Chat and Actions Section */}
      <div className="lg:w-96 flex flex-col">
        {/* Chat Interface */}
        <div className="flex-1 bg-white rounded-lg shadow-md overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Feedback</h3>
            <p className="text-sm text-gray-600 mt-1">
              Describe what you'd like to change
            </p>
          </div>

          <ChatInterface
            messages={messages}
            onSendMessage={handleSendFeedback}
            isProcessing={isRegenerating}
            disabled={disabled}
            placeholder={
              selectedIndices.size > 0
                ? `Feedback for selected ${
                    isStoryboard ? "clips" : "images"
                  }...`
                : "Describe changes for all images..."
            }
          />
        </div>

        {/* Action Buttons */}
        <div className="mt-4 space-y-3">
          <button
            onClick={handleRegenerate}
            disabled={disabled || isRegenerating}
            className="w-full px-6 py-3 bg-yellow-500 text-white font-semibold rounded-lg hover:bg-yellow-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isRegenerating
              ? "Regenerating..."
              : selectedIndices.size > 0
              ? `Regenerate Selected (${selectedIndices.size})`
              : "Regenerate All"}
          </button>

          <button
            onClick={onApprove}
            disabled={disabled || isRegenerating || itemCount === 0}
            className="w-full px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            ✓ Approve &amp; Continue
          </button>
        </div>
      </div>

      {/* Lightbox Modal for Enlarged Image */}
      {enlargedImage && (
        <div
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
          onClick={() => setEnlargedImage(null)}
        >
          <div className="relative max-w-7xl max-h-full">
            <img
              src={enlargedImage}
              alt="Enlarged view"
              className="max-w-full max-h-screen object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setEnlargedImage(null)}
              className="absolute top-4 right-4 w-10 h-10 bg-white rounded-full flex items-center justify-center text-gray-900 text-xl font-bold hover:bg-gray-100"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Story 4: Image Editor Modal */}
      {editingImage && sessionId && (
        <ImageEditor
          imageUrl={editingImage.url}
          imageId={editingImage.index}
          sessionId={sessionId}
          onSave={handleSaveEdited}
          onCancel={handleCancelEdit}
        />
      )}
    </div>
  );
}
