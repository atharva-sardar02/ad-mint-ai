import { getAssetUrl } from "../../utils/url";
import { formatDuration } from "../../utils/time";
import type { VideoOutput } from "../../types/pipeline";

interface VideoGalleryProps {
  video?: VideoOutput;
  durationSeconds?: number;
}

export function VideoGallery({ video, durationSeconds }: VideoGalleryProps) {
  if (!video) {
    return (
      <div className="text-center text-gray-600 py-12 bg-white rounded-lg border">
        <p className="text-lg font-semibold mb-2">Video Generation</p>
        <p className="text-gray-500">
          Video generation kicks off after storyboard approval. Hang tight!
        </p>
      </div>
    );
  }

  const finalVideoUrl = video.final_video?.url
    ? getAssetUrl(video.final_video.url)
    : null;

  const clips = video.clips ?? [];

  return (
    <div className="bg-white rounded-lg border shadow-sm p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Video Output</h2>
          <p className="text-sm text-gray-600 mt-1">
            Review the stitched video and individual clips generated with Veo 3.
          </p>
        </div>
        {durationSeconds && (
          <div className="text-sm text-gray-500">
            Generated in {formatDuration(durationSeconds)}
          </div>
        )}
      </div>

      {finalVideoUrl ? (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            Final Video
          </h3>
          <video
            controls
            className="w-full rounded-lg border border-gray-200 bg-black"
            src={finalVideoUrl}
          >
            Your browser does not support the video tag.
          </video>
          <div className="mt-2 text-sm text-gray-500 flex items-center gap-2">
            <span>Model: {video.model}</span>
            <span className="text-gray-300">|</span>
            <span>Status: {video.status}</span>
          </div>
        </div>
      ) : (
        <div className="border border-blue-200 rounded-lg bg-blue-50 p-4 text-blue-900">
          <p className="font-semibold">Final video pending</p>
          <p className="text-sm text-blue-800 mt-1">
            The stitched video will appear here once all clips are ready.
          </p>
        </div>
      )}

      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3">
          Individual Clips
        </h3>
        <div className="grid gap-4 md:grid-cols-2">
          {clips.length === 0 && (
            <p className="text-sm text-gray-500">
              Clip details will appear once individual renders finish.
            </p>
          )}
          {clips.map((clip) => (
            <div
              key={clip.clip_number}
              className="border border-gray-200 rounded-lg p-4 flex items-center justify-between"
            >
              <div>
                <p className="text-sm font-semibold text-gray-900">
                  Clip {clip.clip_number}
                </p>
                <p className="text-xs text-gray-500">
                  Model: {clip.model || "google/veo-3"}
                </p>
              </div>
              <a
                href={getAssetUrl(clip.url)}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                target="_blank"
                rel="noreferrer"
              >
                Download
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

