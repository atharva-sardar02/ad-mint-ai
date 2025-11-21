/**
 * ImageEditor Component - AC #1, #2, #3, #4
 *
 * Canvas-based image editor with brush/eraser tools for creating masks
 * and inpainting specific regions with AI-generated content.
 *
 * Features:
 * - Brush tool with adjustable size (10-100px)
 * - Eraser tool
 * - Clear mask button
 * - Prompt input for replacement content
 * - Negative prompt (optional, collapsed by default)
 */

import { useEffect, useRef, useState } from "react";
import { Stage, Layer, Image as KonvaImage, Line } from "react-konva";
import useImage from "use-image";

export interface ImageEditorProps {
  imageUrl: string;
  imageId: number;
  sessionId: string;
  onSave: (editedImageUrl: string, version: number, editHistory: string[]) => void;
  onCancel: () => void;
}

interface DrawLine {
  tool: "brush" | "eraser";
  points: number[];
  brushSize: number;
}

export default function ImageEditor({
  imageUrl,
  imageId,
  sessionId,
  onSave,
  onCancel,
}: ImageEditorProps) {
  // Canvas state
  const [image] = useImage(imageUrl, "anonymous");
  const [lines, setLines] = useState<DrawLine[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const stageRef = useRef<any>(null);
  const layerRef = useRef<any>(null);

  // Tool state
  const [tool, setTool] = useState<"brush" | "eraser">("brush");
  const [brushSize, setBrushSize] = useState(30);

  // Prompt state
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState(
    "blurry, low quality, distorted, deformed"
  );
  const [showNegativePrompt, setShowNegativePrompt] = useState(false);

  // Inpainting state
  const [isInpainting, setIsInpainting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Before/after state (set after inpainting completes)
  const [editedImageUrl, setEditedImageUrl] = useState<string | null>(null);
  const [editVersion, setEditVersion] = useState<number | null>(null);
  const [editHistory, setEditHistory] = useState<string[]>([]);

  // Canvas dimensions
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 });

  // Compute canvas size based on image dimensions
  useEffect(() => {
    if (image) {
      const maxWidth = 1024;
      const maxHeight = 768;

      let width = image.width;
      let height = image.height;

      // Scale down if too large
      if (width > maxWidth || height > maxHeight) {
        const scale = Math.min(maxWidth / width, maxHeight / height);
        width = width * scale;
        height = height * scale;
      }

      setCanvasSize({ width, height });
    }
  }, [image]);

  // Mouse/touch event handlers for drawing
  const handleMouseDown = (e: any) => {
    setIsDrawing(true);
    const pos = e.target.getStage().getPointerPosition();
    setLines([...lines, { tool, points: [pos.x, pos.y], brushSize }]);
  };

  const handleMouseMove = (e: any) => {
    if (!isDrawing) return;

    const stage = e.target.getStage();
    const point = stage.getPointerPosition();

    // Add point to current line
    const lastLine = lines[lines.length - 1];
    lastLine.points = lastLine.points.concat([point.x, point.y]);

    // Replace last line with updated version
    const newLines = lines.slice(0, -1).concat(lastLine);
    setLines(newLines);
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  // Clear all mask lines
  const handleClearMask = () => {
    setLines([]);
    setError(null);
  };

  // Convert canvas mask to base64
  const getMaskBase64 = (): string | null => {
    if (!image || !stageRef.current) return null;

    // Create offscreen canvas for mask
    const maskCanvas = document.createElement("canvas");
    maskCanvas.width = image.width;
    maskCanvas.height = image.height;
    const ctx = maskCanvas.getContext("2d")!;

    // Fill with black (preserve)
    ctx.fillStyle = "black";
    ctx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);

    // Scale factor between display canvas and original image
    const scaleX = image.width / canvasSize.width;
    const scaleY = image.height / canvasSize.height;

    // Draw white (replace) where user drew brush strokes
    ctx.strokeStyle = "white";
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    for (const line of lines) {
      if (line.tool === "brush") {
        ctx.lineWidth = line.brushSize * Math.max(scaleX, scaleY);
        ctx.globalCompositeOperation = "source-over";
      } else {
        // Eraser draws black
        ctx.lineWidth = line.brushSize * Math.max(scaleX, scaleY);
        ctx.globalCompositeOperation = "destination-out";
      }

      ctx.beginPath();
      for (let i = 0; i < line.points.length - 1; i += 2) {
        const x = line.points[i] * scaleX;
        const y = line.points[i + 1] * scaleY;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    }

    // Convert to base64
    const imageData = ctx.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
    const binaryData = new Uint8Array(maskCanvas.width * maskCanvas.height);

    // Convert RGBA to binary (0 or 255)
    for (let i = 0; i < binaryData.length; i++) {
      const pixelValue = imageData.data[i * 4]; // Red channel (grayscale)
      binaryData[i] = pixelValue > 128 ? 255 : 0;
    }

    // Convert to base64
    const base64 = btoa(String.fromCharCode(...binaryData));
    return base64;
  };

  // Handle inpainting execution
  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError("Prompt is required");
      return;
    }

    if (lines.length === 0) {
      setError("Please draw a mask region to replace");
      return;
    }

    setError(null);
    setIsInpainting(true);

    try {
      const maskData = getMaskBase64();
      if (!maskData) {
        throw new Error("Failed to generate mask data");
      }

      // Call inpainting API
      const { inpaintImage } = await import("../../services/interactive-api");
      const response = await inpaintImage(
        sessionId,
        imageId,
        maskData,
        prompt,
        showNegativePrompt ? negativePrompt : undefined
      );

      // Set edited image for before/after view
      setEditedImageUrl(response.edited_image_url);
      setEditVersion(response.version);
      setEditHistory(response.edit_history);
    } catch (err: any) {
      console.error("Inpainting failed:", err);
      setError(err.message || "Failed to inpaint image. Please try again.");
    } finally {
      setIsInpainting(false);
    }
  };

  // Handle "Use Edited" button
  const handleUseEdited = () => {
    if (editedImageUrl && editVersion !== null) {
      onSave(editedImageUrl, editVersion, editHistory);
    }
  };

  // Handle "Keep Original" button
  const handleKeepOriginal = () => {
    // Reset to drawing mode
    setEditedImageUrl(null);
    setEditVersion(null);
    setEditHistory([]);
  };

  // If we have edited image, show before/after comparison (AC #6)
  if (editedImageUrl) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-xl font-semibold">Before / After Comparison</h2>
            <button
              onClick={onCancel}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          {/* Before/After Images */}
          <div className="p-6">
            <div className="grid grid-cols-2 gap-4 mb-6">
              {/* Original */}
              <div>
                <p className="text-sm font-medium mb-2 text-center">Original</p>
                <img
                  src={imageUrl}
                  alt="Original"
                  className="w-full h-auto rounded border"
                />
              </div>

              {/* Edited */}
              <div>
                <p className="text-sm font-medium mb-2 text-center">
                  Edited (Version {editVersion})
                </p>
                <img
                  src={editedImageUrl}
                  alt="Edited"
                  className="w-full h-auto rounded border"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 justify-center">
              <button
                onClick={handleKeepOriginal}
                className="px-6 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium"
              >
                Keep Original
              </button>
              <button
                onClick={handleUseEdited}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
              >
                Use Edited
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Drawing mode (AC #1, #2, #3, #4)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">Edit Image</h2>
          <button
            onClick={onCancel}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        {/* Main Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Canvas Area (2/3 width) */}
            <div className="lg:col-span-2">
              <div className="border rounded-lg bg-gray-50 flex items-center justify-center p-4">
                {image ? (
                  <Stage
                    ref={stageRef}
                    width={canvasSize.width}
                    height={canvasSize.height}
                    onMouseDown={handleMouseDown}
                    onMousemove={handleMouseMove}
                    onMouseup={handleMouseUp}
                    onTouchStart={handleMouseDown}
                    onTouchMove={handleMouseMove}
                    onTouchEnd={handleMouseUp}
                    className="cursor-crosshair"
                  >
                    <Layer ref={layerRef}>
                      {/* Original Image */}
                      <KonvaImage
                        image={image}
                        width={canvasSize.width}
                        height={canvasSize.height}
                      />

                      {/* Mask Lines */}
                      {lines.map((line, i) => (
                        <Line
                          key={i}
                          points={line.points}
                          stroke={line.tool === "brush" ? "rgba(255, 0, 0, 0.5)" : "rgba(0, 0, 0, 0.8)"}
                          strokeWidth={line.brushSize}
                          tension={0.5}
                          lineCap="round"
                          lineJoin="round"
                          globalCompositeOperation={
                            line.tool === "brush" ? "source-over" : "destination-out"
                          }
                        />
                      ))}
                    </Layer>
                  </Stage>
                ) : (
                  <p className="text-gray-500">Loading image...</p>
                )}
              </div>

              {/* Tools */}
              <div className="mt-4 flex flex-wrap items-center gap-4">
                {/* Brush/Eraser Toggle */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setTool("brush")}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      tool === "brush"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 hover:bg-gray-300"
                    }`}
                  >
                    Brush
                  </button>
                  <button
                    onClick={() => setTool("eraser")}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      tool === "eraser"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 hover:bg-gray-300"
                    }`}
                  >
                    Eraser
                  </button>
                </div>

                {/* Brush Size Slider */}
                <div className="flex items-center gap-3 flex-1 min-w-[200px]">
                  <label className="text-sm font-medium whitespace-nowrap">
                    Size: {brushSize}px
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    value={brushSize}
                    onChange={(e) => setBrushSize(Number(e.target.value))}
                    className="flex-1"
                  />
                </div>

                {/* Clear Mask */}
                <button
                  onClick={handleClearMask}
                  className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg font-medium"
                >
                  Clear Mask
                </button>
              </div>
            </div>

            {/* Prompt Panel (1/3 width) */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Replacement Prompt *
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe what should replace the masked region..."
                  className="w-full px-3 py-2 border rounded-lg resize-none h-24"
                  disabled={isInpainting}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Example: "red sports car", "sunset beach background"
                </p>
              </div>

              {/* Negative Prompt (Collapsible) */}
              <div>
                <button
                  onClick={() => setShowNegativePrompt(!showNegativePrompt)}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium mb-2"
                >
                  {showNegativePrompt ? "Hide" : "Show"} Negative Prompt
                </button>

                {showNegativePrompt && (
                  <textarea
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    placeholder="What to avoid..."
                    className="w-full px-3 py-2 border rounded-lg resize-none h-20 text-sm"
                    disabled={isInpainting}
                  />
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  {error}
                </div>
              )}

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={isInpainting || !prompt.trim() || lines.length === 0}
                className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-medium"
              >
                {isInpainting ? "Generating..." : "Generate Replacement"}
              </button>

              {/* Instructions */}
              <div className="text-xs text-gray-600 space-y-1 pt-4 border-t">
                <p className="font-medium">Instructions:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Use Brush to mark regions to replace</li>
                  <li>Use Eraser to fix mistakes</li>
                  <li>Adjust brush size with slider</li>
                  <li>Enter prompt describing replacement</li>
                  <li>Click Generate to see result</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
