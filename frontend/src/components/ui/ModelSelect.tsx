/**
 * ModelSelect component with tooltip support for video models.
 */
import React, { useId, useState } from "react";
import { Select } from "./Select";
import type { VideoModel } from "../../lib/models/videoModels";
import { DEFAULT_MODEL } from "../../lib/models/videoModels";

export interface ModelSelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "options"> {
  label?: string;
  models: VideoModel[];
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
}

/**
 * Tooltip component for model information.
 */
const ModelTooltip: React.FC<{ model: VideoModel; children: React.ReactNode }> = ({
  model,
  children,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="inline-flex items-center cursor-help"
      >
        {children}
      </div>
      {showTooltip && (
        <div className="absolute z-50 w-80 p-3 mt-1 text-xs text-white bg-gray-900 rounded-lg shadow-xl left-0 top-full pointer-events-none">
          <div className="font-semibold mb-2 text-sm">{model.label}</div>
          <div className="mb-2 text-gray-300">{model.description}</div>
          <div className="border-t border-gray-700 pt-2 mt-2 space-y-1">
            <div>
              <span className="font-medium text-gray-400">Max Length:</span>{" "}
              <span className="text-white">{model.maxLength}</span>
            </div>
            <div>
              <span className="font-medium text-gray-400">Input:</span>{" "}
              <span className="text-white">{model.inputTypes.join(", ")}</span>
            </div>
            <div>
              <span className="font-medium text-gray-400">Audio:</span>{" "}
              <span className="text-white">{model.audio ? "Yes" : "No"}</span>
            </div>
            <div className="mt-2 pt-2 border-t border-gray-700">
              <div className="mb-1">
                <span className="font-medium text-green-400">Strengths:</span>{" "}
                <span className="text-gray-300">{model.strengths}</span>
              </div>
              <div>
                <span className="font-medium text-amber-400">Limitations:</span>{" "}
                <span className="text-gray-300">{model.weaknesses}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * ModelSelect component with tooltip support.
 */
export const ModelSelect: React.FC<ModelSelectProps> = ({
  label,
  models,
  value,
  onChange,
  disabled = false,
  required = false,
  placeholder = "Auto (use default)",
  className = "",
  id,
  ...props
}) => {
  const generatedId = useId();
  const selectId = id ?? generatedId;

  // Convert models to options format
  const options = models.map((model) => ({
    value: model.value,
    label: model.label,
  }));

  // Add placeholder option
  const allOptions = [
    { value: "", label: placeholder },
    ...options,
  ];

  // Find selected model for tooltip, or use default model if none selected
  const selectedModel = models.find((m) => m.value === value);
  const tooltipModel = selectedModel || models.find((m) => m.value === DEFAULT_MODEL);

  return (
    <div className="w-full">
      <div className="flex items-center gap-2 mb-1">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}
        {tooltipModel && (
          <ModelTooltip model={tooltipModel}>
            <svg
              className="w-4 h-4 text-gray-400 cursor-help"
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
          </ModelTooltip>
        )}
      </div>
      <Select
        id={selectId}
        label="" // Label is handled above
        options={allOptions}
        value={value || ""}
        onChange={onChange}
        disabled={disabled}
        required={required}
        className={className}
        {...props}
      />
    </div>
  );
};

