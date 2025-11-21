/**
 * VideoPlayer Component
 * 
 * Displays a video with controls, download button, and fullscreen support.
 */
import React, { useRef, useState } from "react";

interface VideoPlayerProps {
  videoPath: string;
  title: string;
  description?: string;
  className?: string;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoPath,
  title,
  description,
  className = "",
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  
  // Handle different path formats
  let videoUrl: string;
  if (videoPath.startsWith("http")) {
    // Already a full URL
    videoUrl = videoPath;
  } else if (videoPath.includes(":/") || videoPath.includes(":\\")) {
    // Absolute file path (e.g., D:/gauntlet-ai/ad-mint-ai/backend/temp/...)
    // Extract the relative path starting from 'temp' or 'output'
    const normalized = videoPath.replace(/\\/g, "/");
    const tempIndex = normalized.indexOf("/temp/");
    const outputIndex = normalized.indexOf("/output/");
    
    if (tempIndex !== -1) {
      videoUrl = `${apiUrl}${normalized.substring(tempIndex)}`;
    } else if (outputIndex !== -1) {
      videoUrl = `${apiUrl}${normalized.substring(outputIndex)}`;
    } else {
      // Fallback: try to find the filename
      const parts = normalized.split("/");
      videoUrl = `${apiUrl}/temp/${parts[parts.length - 1]}`;
    }
  } else {
    // Relative path
    const cleanPath = videoPath.startsWith("/") ? videoPath : `/${videoPath}`;
    videoUrl = `${apiUrl}${cleanPath}`;
  }
  
  console.log("VideoPlayer - Original path:", videoPath);
  console.log("VideoPlayer - Constructed URL:", videoUrl);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = videoUrl;
    link.download = `${title.replace(/\s+/g, "_")}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-md overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
      </div>

      {/* Video */}
      <div className="relative bg-black aspect-video">
        <video
          ref={videoRef}
          className="w-full h-full"
          src={videoUrl}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => setIsPlaying(false)}
          controls
        >
          Your browser does not support the video tag.
        </video>
      </div>

      {/* Controls Footer */}
      <div className="p-4 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Play/Pause Button */}
            <button
              onClick={handlePlayPause}
              className="p-2 rounded-full hover:bg-gray-200 transition-colors"
              aria-label={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? (
                <svg className="w-6 h-6 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>

            {/* Time Display */}
            <div className="text-sm text-gray-600">
              <span>{formatTime(currentTime)}</span>
              <span className="mx-1">/</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Download Button */}
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            <span className="text-sm font-medium">Download</span>
          </button>
        </div>
      </div>
    </div>
  );
};


