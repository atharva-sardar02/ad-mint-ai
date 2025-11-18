/**
 * BasicSettingsPanel component for managing basic video generation settings.
 * Displays an expandable panel with basic generation options.
 */
import React, { useState } from "react";
import { Select } from "../ui/Select";
import { ModelSelect } from "../ui/ModelSelect";
import { VIDEO_MODELS } from "../../lib/models/videoModels";

export interface BasicSettings {
  useSingleClip: boolean;
  useLlm: boolean;
  model: string;
  targetDuration: number;
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
  const [isExpanded, setIsExpanded] = useState(false); // Default to collapsed

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

  const handleTargetDurationChange = (value: number) => {
    if (disabled) return;
    onChange({
      ...settings,
      targetDuration: value,
    });
  };

  return (
    <div className="border border-gray-200 rounded-md bg-gray-50">
      <div className="p-3">
        <div className="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
          <div className="flex items-center">
            <h4 className="text-sm font-medium text-gray-700">
              Basic Settings
            </h4>
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
          <button
            type="button"
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            {isExpanded ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-3 pb-3 space-y-3 border-t border-gray-200">
          {/* Single Clip Mode Toggle */}
          <div className="flex items-center space-x-2 pt-3">
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
            <ModelSelect
              label="Video Model"
              id="basic-model"
              models={VIDEO_MODELS}
              value={settings.model || ""}
              onChange={(e) => handleModelChange(e.target.value)}
              disabled={disabled}
              required={settings.useSingleClip}
              placeholder={settings.useSingleClip ? "Select a model (required)" : undefined}
            />
          </div>

          {/* Target Duration */}
          <div>
            <Select
              label="Target Duration (seconds)"
              id="basic-targetDuration"
              value={settings.targetDuration.toString()}
              onChange={(e) =>
                handleTargetDurationChange(parseInt(e.target.value, 10))
              }
              disabled={disabled}
              options={[
                { value: "9", label: "9 seconds" },
                { value: "12", label: "12 seconds" },
                { value: "15", label: "15 seconds (default)" },
                { value: "18", label: "18 seconds" },
                { value: "21", label: "21 seconds" },
                { value: "24", label: "24 seconds" },
                { value: "30", label: "30 seconds" },
                { value: "45", label: "45 seconds" },
                { value: "60", label: "60 seconds" },
              ]}
            />
            <p className="mt-1 text-xs text-gray-500">
              LLM will decide number of scenes and duration per scene (max 7s per scene)
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

