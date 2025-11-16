/**
 * BasicSettingsPanel component for managing basic video generation settings.
 * Displays an expandable panel with basic generation options.
 */
import React, { useState } from "react";
import { Button } from "../ui/Button";
import { Select } from "../ui/Select";

export interface BasicSettings {
  useSingleClip: boolean;
  useLlm: boolean;
  model: string;
  numClips: number;
}

export interface BasicSettingsPanelProps {
  settings: BasicSettings;
  onChange: (settings: BasicSettings) => void;
  disabled?: boolean;
}

/**
 * Tooltip component for help text.
 */
const Tooltip: React.FC<{ content: string; children: React.ReactNode }> = ({
  content,
  children,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {children}
      </div>
      {showTooltip && (
        <div className="absolute z-10 w-64 p-2 mt-2 text-xs text-white bg-gray-900 rounded shadow-lg left-0">
          {content}
        </div>
      )}
    </div>
  );
};

/**
 * BasicSettingsPanel component.
 * Displays an expandable panel with basic generation settings.
 */
export const BasicSettingsPanel: React.FC<BasicSettingsPanelProps> = ({
  settings,
  onChange,
  disabled = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(true); // Default to expanded

  const handleSingleClipChange = (value: boolean) => {
    if (disabled) return;
    onChange({
      ...settings,
      useSingleClip: value,
      useLlm: value ? false : settings.useLlm, // Disable LLM when single clip is enabled
    });
  };

  const handleLlmChange = (value: boolean) => {
    if (disabled) return;
    onChange({
      ...settings,
      useLlm: value,
      useSingleClip: value ? false : settings.useSingleClip, // Disable single clip when LLM is enabled
    });
  };

  const handleModelChange = (value: string) => {
    if (disabled) return;
    onChange({
      ...settings,
      model: value,
    });
  };

  const handleNumClipsChange = (value: number) => {
    if (disabled) return;
    onChange({
      ...settings,
      numClips: value,
    });
  };

  return (
    <div className="mb-6 border border-gray-200 rounded-lg bg-white">
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <h3 className="text-lg font-semibold text-gray-900">
              Basic Settings
            </h3>
            <Tooltip content="Configure basic video generation options: generation mode, model selection, and number of clips.">
              <svg
                className="w-5 h-5 ml-2 text-gray-400 cursor-help"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </Tooltip>
          </div>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm"
          >
            {isExpanded ? "Collapse" : "Expand"}
          </Button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-200 space-y-4">
          {/* Single Clip Mode Toggle */}
          <div className="flex items-center space-x-2 pt-4">
            <input
              type="checkbox"
              id="basic-useSingleClip"
              checked={settings.useSingleClip}
              onChange={(e) => handleSingleClipChange(e.target.checked)}
              disabled={disabled}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label
              htmlFor="basic-useSingleClip"
              className="text-sm font-medium text-gray-700"
            >
              Generate single clip (bypass pipeline)
            </label>
          </div>

          {/* LLM Enhancement Toggle */}
          {!settings.useSingleClip && (
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="basic-useLlm"
                checked={settings.useLlm}
                onChange={(e) => handleLlmChange(e.target.checked)}
                disabled={disabled}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label
                htmlFor="basic-useLlm"
                className="text-sm font-medium text-gray-700"
              >
                Use LLM enhancement (recommended)
              </label>
            </div>
          )}

          {/* Model Selection */}
          <div>
            <Select
              label="Video Model"
              id="basic-model"
              value={settings.model || ""}
              onChange={(e) => handleModelChange(e.target.value)}
              disabled={disabled}
              required={settings.useSingleClip}
              options={[
                {
                  value: "",
                  label: settings.useSingleClip
                    ? "Select a model (required)"
                    : "Auto (use default)",
                },
                {
                  value: "bytedance/seedance-1-lite",
                  label: "Seedance-1-Lite (Primary)",
                },
                {
                  value: "minimax-ai/minimax-video-01",
                  label: "Minimax Video-01",
                },
                { value: "klingai/kling-video", label: "Kling 1.5" },
                {
                  value: "runway/gen3-alpha-turbo",
                  label: "Runway Gen-3 Alpha Turbo",
                },
                { value: "openai/sora-2", label: "Sora-2" },
              ]}
            />
          </div>

          {/* Number of Clips */}
          <div>
            <Select
              label="Number of Clips"
              id="basic-numClips"
              value={settings.numClips.toString()}
              onChange={(e) =>
                handleNumClipsChange(parseInt(e.target.value, 10))
              }
              disabled={disabled}
              options={Array.from({ length: 10 }, (_, i) => ({
                value: (i + 1).toString(),
                label: (i + 1).toString(),
              }))}
            />
          </div>
        </div>
      )}
    </div>
  );
};

