/**
 * CoherenceSettingsPanel component for managing video generation coherence settings.
 * Displays an expandable panel with checkboxes for various coherence techniques.
 */
import React, { useState } from "react";

export interface CoherenceSettings {
  seed_control: boolean;
  ip_adapter_reference: boolean; // IP-Adapter with reference images (same real images for all clips)
  ip_adapter_sequential: boolean; // IP-Adapter with sequential images (reference + previous clip images)
  lora: boolean;
  enhanced_planning: boolean;
  vbench_quality_control: boolean;
  automatic_regeneration: boolean; // Automatically regenerate clips that fail quality thresholds
  post_processing_enhancement: boolean;
  color_grading: boolean; // Apply color grading based on brand style
  controlnet: boolean;
  csfd_detection: boolean;
}

export interface CoherenceSettingsPanelProps {
  settings: CoherenceSettings;
  onChange: (settings: CoherenceSettings) => void;
  errors?: ValidationErrors;
  disabled?: boolean;
  showWarnings?: boolean;
}

export interface ValidationErrors {
  [key: string]: string | undefined;
}

/**
 * Validates coherence settings and returns validation errors.
 * Checks for dependency violations and incompatible combinations.
 */
export const validateCoherenceSettings = (
  settings: CoherenceSettings
): ValidationErrors => {
  const errors: ValidationErrors = {};

  // Check dependencies
  TECHNIQUE_INFO.forEach((technique) => {
    if (settings[technique.key] && technique.requires && technique.requires.length > 0) {
      const missingDeps = technique.requires.filter((dep) => !settings[dep]);
      if (missingDeps.length > 0) {
        const depLabels = missingDeps.map(
          (dep) => TECHNIQUE_INFO.find((t) => t.key === dep)?.label || dep
        );
        errors[technique.key] = `Requires ${depLabels.join(" and ")} to be enabled`;
      }
    }

    // Check incompatibilities
    if (settings[technique.key] && technique.incompatibleWith && technique.incompatibleWith.length > 0) {
      const incompatibleEnabled = technique.incompatibleWith.filter(
        (incompatible) => settings[incompatible]
      );
      if (incompatibleEnabled.length > 0) {
        const incompatibleLabels = incompatibleEnabled.map(
          (inc) => TECHNIQUE_INFO.find((t) => t.key === inc)?.label || inc
        );
        errors[technique.key] = `Incompatible with ${incompatibleLabels.join(" and ")}`;
      }
    }
  });

  return errors;
};

/**
 * Gets warning messages for recommended combinations.
 * Returns warnings if user has disabled recommended settings or enabled non-recommended ones.
 */
export const getCoherenceWarnings = (
  settings: CoherenceSettings
): string[] => {
  const warnings: string[] = [];

  // Warn if recommended settings that are also default-enabled are disabled
  const disabledRecommended = TECHNIQUE_INFO.filter(
    (t) => t.recommended && t.defaultEnabled && !settings[t.key]
  );
  if (disabledRecommended.length > 0) {
    warnings.push(
      `Recommended settings are disabled: ${disabledRecommended.map((t) => t.label).join(", ")}. This may affect video quality.`
    );
  }

  // Warn if non-recommended advanced settings are enabled
  const enabledAdvanced = TECHNIQUE_INFO.filter(
    (t) => !t.recommended && settings[t.key]
  );
  if (enabledAdvanced.length > 0) {
    warnings.push(
      `Advanced settings enabled: ${enabledAdvanced.map((t) => t.label).join(", ")}. These may increase generation time and cost.`
    );
  }

  return warnings;
};

interface TechniqueInfo {
  key: keyof CoherenceSettings;
  label: string;
  description: string;
  defaultEnabled: boolean;
  recommended: boolean;
  timeImpact?: string;
  costImpact?: string;
  tooltip: string;
  requires?: keyof CoherenceSettings[];
  incompatibleWith?: keyof CoherenceSettings[];
  implemented: boolean; // Whether this feature is actually implemented
  comingSoonMessage?: string; // Optional message for unimplemented features
}

const TECHNIQUE_INFO: TechniqueInfo[] = [
  {
    key: "seed_control",
    label: "Seed Control",
    description: "Ensures consistent visual style across scenes using seed values",
    defaultEnabled: true,
    recommended: true,
    timeImpact: "Low",
    costImpact: "None",
    tooltip: "Seed control maintains visual consistency by reusing seed values across video scenes. This is a lightweight technique with no additional cost.",
    requires: [],
    incompatibleWith: [],
    implemented: true, // ✅ Story 7.1 - Implemented
  },
  {
    key: "ip_adapter_reference",
    label: "IP-Adapter (Reference Images)",
    description: "Uses the same real reference image(s) for all video clip generations to maintain character/product identity",
    defaultEnabled: false, // Enabled by default if entities detected (handled by backend)
    recommended: true,
    timeImpact: "Medium",
    costImpact: "Low",
    tooltip: "IP-Adapter with reference images: Provides the same real image(s) to all video clip generations. This maintains consistent appearance of characters or products across different scenes using static reference images. Requires Enhanced LLM Planning to be enabled.",
    requires: ["enhanced_planning"],
    incompatibleWith: ["ip_adapter_sequential"], // Can't use both approaches simultaneously
    implemented: false, // ⏸️ Story 7.3 - Backlog
    comingSoonMessage: "Coming soon - Story 7.3",
  },
  {
    key: "ip_adapter_sequential",
    label: "IP-Adapter (Sequential Images)",
    description: "Uses reference images + images from previous generated clips for progressive consistency",
    defaultEnabled: false,
    recommended: false,
    timeImpact: "Medium-High",
    costImpact: "Low",
    tooltip: "IP-Adapter with sequential images: Provides reference images plus images extracted from previously generated clips. This creates progressive visual consistency where each clip builds upon the previous one. Useful for comparing sequential vs static reference approaches. Requires Enhanced LLM Planning to be enabled. Incompatible with Reference Images mode.",
    requires: ["enhanced_planning"],
    incompatibleWith: ["ip_adapter_reference"], // Can't use both approaches simultaneously
    implemented: false, // ⏸️ Story 7.3 - Backlog
    comingSoonMessage: "Coming soon - Story 7.3",
  },
  {
    key: "lora",
    label: "LoRA Training",
    description: "Uses trained LoRA models for character/product consistency",
    defaultEnabled: false,
    recommended: false,
    timeImpact: "High",
    costImpact: "Medium",
    tooltip: "LoRA (Low-Rank Adaptation) training provides fine-tuned models for specific characters or products. Requires a pre-trained LoRA model to be available. Requires Enhanced LLM Planning to be enabled.",
    requires: ["enhanced_planning"],
    incompatibleWith: [],
    implemented: false, // ⏸️ Story 7.4 - Backlog
    comingSoonMessage: "Coming soon - Story 7.4",
  },
  {
    key: "enhanced_planning",
    label: "Enhanced LLM Planning",
    description: "Uses advanced LLM techniques for better scene planning and coherence",
    defaultEnabled: true,
    recommended: true,
    timeImpact: "Low",
    costImpact: "Low",
    tooltip: "Enhanced LLM planning improves scene breakdown and visual prompt generation for better coherence. Recommended for all video generations.",
    requires: [],
    incompatibleWith: [],
    implemented: false, // ⏸️ Story 7.2 - Backlog
    comingSoonMessage: "Coming soon - Story 7.2",
  },
  {
    key: "vbench_quality_control",
    label: "VBench Quality Control",
    description: "Automated quality assessment using VBench metrics",
    defaultEnabled: true,
    recommended: true,
    timeImpact: "Medium",
    costImpact: "Low",
    tooltip: "VBench quality control automatically evaluates generated video clips using research-backed quality metrics to ensure high standards. Quality scores are displayed for each clip.",
    requires: [],
    incompatibleWith: [],
    implemented: true, // ✅ Story 7.6 - Implemented
  },
  {
    key: "automatic_regeneration",
    label: "Automatic Regeneration",
    description: "Automatically regenerate clips that fail quality thresholds",
    defaultEnabled: false,
    recommended: false,
    timeImpact: "High",
    costImpact: "Medium",
    tooltip: "When enabled, clips that fail quality thresholds will be automatically regenerated up to 2 times. This can significantly increase generation time and cost. Requires VBench Quality Control to be enabled.",
    requires: ["vbench_quality_control"],
    incompatibleWith: [],
    implemented: true, // ✅ Story 7.6 - Implemented
  },
  {
    key: "post_processing_enhancement",
    label: "Post-Processing Enhancement",
    description: "Applies visual enhancements to final video",
    defaultEnabled: true,
    recommended: true,
    timeImpact: "Low",
    costImpact: "None",
    tooltip: "Post-processing enhancement applies contrast adjustments and other visual improvements to the final video output.",
    requires: [],
    incompatibleWith: [],
    implemented: false, // ⏸️ Story 7.6 - Backlog
    comingSoonMessage: "Coming soon - Story 7.6",
  },
  {
    key: "color_grading",
    label: "Color Grading",
    description: "Apply color grading based on brand style (cinematic, luxury, vibrant)",
    defaultEnabled: false,
    recommended: false,
    timeImpact: "Low",
    costImpact: "None",
    tooltip: "Color grading applies brand-specific color treatments to the final video. Styles include cinematic (desaturated, cooler tones), luxury (warm tones, enhanced contrast), and vibrant (enhanced saturation, bright colors).",
    requires: [],
    incompatibleWith: [],
    implemented: true, // ✅ Implemented
  },
  {
    key: "controlnet",
    label: "ControlNet for Compositional Consistency",
    description: "Advanced technique for maintaining compositional consistency (experimental)",
    defaultEnabled: false,
    recommended: false,
    timeImpact: "High",
    costImpact: "Medium",
    tooltip: "ControlNet provides advanced control over composition and structure across scenes. This is an experimental feature and may increase generation time significantly. Requires Enhanced LLM Planning to be enabled. Incompatible with CSFD Detection.",
    requires: ["enhanced_planning"],
    incompatibleWith: ["csfd_detection"],
    implemented: false, // ⏸️ Story 7.8 - Backlog
    comingSoonMessage: "Coming soon - Story 7.8",
  },
  {
    key: "csfd_detection",
    label: "CSFD Character Consistency Detection",
    description: "Cross-scene feature detection for character consistency (character-driven ads only)",
    defaultEnabled: false,
    recommended: false,
    timeImpact: "Medium",
    costImpact: "Low",
    tooltip: "CSFD (Cross-Scene Feature Detection) analyzes and maintains character consistency across scenes. Best suited for character-driven advertisements. Requires Enhanced LLM Planning to be enabled. Incompatible with ControlNet.",
    requires: ["enhanced_planning"],
    incompatibleWith: ["controlnet"],
    implemented: false, // ⏸️ Story 7.7 - Backlog
    comingSoonMessage: "Coming soon - Story 7.7",
  },
];

/**
 * Simple tooltip component for displaying detailed information on hover.
 */
const Tooltip: React.FC<{ content: string; children: React.ReactNode }> = ({
  content,
  children,
}) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="cursor-help"
      >
        {children}
      </div>
      {isVisible && (
        <div
          className="absolute z-50 w-64 p-2 mt-1 text-xs text-white bg-gray-900 rounded-md shadow-lg pointer-events-none"
          style={{ bottom: "100%", left: "50%", transform: "translateX(-50%)" }}
        >
          {content}
          <div
            className="absolute w-0 h-0 border-4 border-transparent border-t-gray-900"
            style={{ top: "100%", left: "50%", transform: "translateX(-50%)" }}
          />
        </div>
      )}
    </div>
  );
};

/**
 * CoherenceSettingsPanel component.
 * Displays an expandable panel with checkboxes for coherence techniques.
 */
export const CoherenceSettingsPanel: React.FC<CoherenceSettingsPanelProps> = ({
  settings,
  onChange,
  errors = {},
  disabled = false,
  showWarnings = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const warnings = showWarnings ? getCoherenceWarnings(settings) : [];

  const handleToggle = (key: keyof CoherenceSettings) => {
    if (disabled) return;
    
    // Prevent toggling unimplemented features
    const technique = TECHNIQUE_INFO.find((t) => t.key === key);
    if (technique && !technique.implemented) {
      return;
    }
    
    const newSettings = {
      ...settings,
      [key]: !settings[key],
    };
    
    // If disabling vbench_quality_control, also disable automatic_regeneration
    if (key === "vbench_quality_control" && !newSettings.vbench_quality_control) {
      newSettings.automatic_regeneration = false;
    }
    
    onChange(newSettings);
  };

  const isTechniqueDisabled = (technique: TechniqueInfo): boolean => {
    if (disabled) return true;

    // Disable if feature is not implemented yet
    if (!technique.implemented) {
      return true;
    }

    // Check if required dependencies are not met
    if (technique.requires && technique.requires.length > 0) {
      const missingDeps = technique.requires.filter((dep) => !settings[dep]);
      if (missingDeps.length > 0) {
        return true;
      }
    }

    // Check if incompatible techniques are enabled
    if (technique.incompatibleWith && technique.incompatibleWith.length > 0) {
      const incompatibleEnabled = technique.incompatibleWith.some(
        (incompatible) => settings[incompatible]
      );
      if (incompatibleEnabled) {
        return true;
      }
    }

    return false;
  };

  const getDisabledReason = (technique: TechniqueInfo): string | null => {
    // First check if feature is not implemented
    if (!technique.implemented) {
      return technique.comingSoonMessage || "Coming soon";
    }

    if (technique.requires && technique.requires.length > 0) {
      const missingDeps = technique.requires.filter((dep) => !settings[dep]);
      if (missingDeps.length > 0) {
        const depLabels = missingDeps.map(
          (dep) => TECHNIQUE_INFO.find((t) => t.key === dep)?.label || dep
        );
        return `Requires: ${depLabels.join(", ")}`;
      }
    }

    if (technique.incompatibleWith && technique.incompatibleWith.length > 0) {
      const incompatibleEnabled = technique.incompatibleWith.filter(
        (incompatible) => settings[incompatible]
      );
      if (incompatibleEnabled.length > 0) {
        const incompatibleLabels = incompatibleEnabled.map(
          (inc) => TECHNIQUE_INFO.find((t) => t.key === inc)?.label || inc
        );
        return `Incompatible with: ${incompatibleLabels.join(", ")}`;
      }
    }

    return null;
  };

  return (
    <div className="border border-gray-200 rounded-md bg-gray-50">
      <div className="p-3">
        <div className="flex items-center justify-between cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
          <div className="flex items-center">
            <h4 className="text-sm font-medium text-gray-700">
              Coherence Settings
            </h4>
            <Tooltip content="Configure which coherence techniques are applied to your video generation. Some techniques have dependencies or may increase generation time and cost.">
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
        <div className="px-3 pb-3 border-t border-gray-200">
          {warnings.length > 0 && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-md">
              <div className="flex items-start">
                <svg
                  className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5 text-amber-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-amber-800 mb-1">
                    Recommendations
                  </h4>
                  <ul className="text-sm text-amber-700 space-y-1">
                    {warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
          <div className="mt-4 space-y-4">
            {TECHNIQUE_INFO.map((technique) => {
              const isDisabled = isTechniqueDisabled(technique);
              const disabledReason = getDisabledReason(technique);
              const isChecked = settings[technique.key];
              const hasError = !!errors[technique.key];

              return (
                <div
                  key={technique.key}
                  className={`p-3 rounded-md border ${
                    hasError
                      ? "border-red-300 bg-red-50"
                      : isDisabled
                      ? "border-gray-200 bg-gray-50 opacity-60"
                      : "border-gray-200 bg-white"
                  }`}
                >
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id={`coherence-${technique.key}`}
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggle(technique.key)}
                        disabled={isDisabled || disabled}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-describedby={
                          disabledReason
                            ? `${technique.key}-reason`
                            : technique.description
                            ? `${technique.key}-description`
                            : undefined
                        }
                      />
                    </div>
                    <div className="ml-3 flex-1">
                      <div className="flex items-center">
                        <label
                          htmlFor={`coherence-${technique.key}`}
                          className={`text-sm font-medium ${
                            isDisabled
                              ? "text-gray-400 cursor-not-allowed"
                              : "text-gray-900 cursor-pointer"
                          }`}
                        >
                          {technique.label}
                        </label>
                        {technique.recommended && (
                          <span className="ml-2 px-2 py-0.5 text-xs font-medium text-green-700 bg-green-100 rounded">
                            Recommended
                          </span>
                        )}
                        {technique.defaultEnabled && !isChecked && (
                          <span className="ml-2 px-2 py-0.5 text-xs font-medium text-gray-600 bg-gray-100 rounded">
                            Default: Enabled
                          </span>
                        )}
                        <Tooltip content={technique.tooltip}>
                          <svg
                            className="w-4 h-4 ml-2 text-gray-400 cursor-help"
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
                      <p
                        id={`${technique.key}-description`}
                        className={`mt-1 text-sm ${
                          isDisabled && !technique.implemented
                            ? "text-gray-400"
                            : "text-gray-600"
                        }`}
                      >
                        {technique.description}
                      </p>
                      <div
                        className={`mt-2 flex flex-wrap gap-2 text-xs ${
                          isDisabled && !technique.implemented
                            ? "text-gray-400"
                            : "text-gray-500"
                        }`}
                      >
                        {technique.timeImpact && (
                          <span>
                            ⏱️ Time: {technique.timeImpact}
                          </span>
                        )}
                        {technique.costImpact && (
                          <span>
                            💰 Cost: {technique.costImpact}
                          </span>
                        )}
                      </div>
                      {disabledReason && (
                        <p
                          id={`${technique.key}-reason`}
                          className={`mt-2 text-xs ${
                            !technique.implemented
                              ? "text-gray-500 italic"
                              : "text-amber-600"
                          }`}
                        >
                          {disabledReason}
                        </p>
                      )}
                      {hasError && (
                        <p className="mt-2 text-xs text-red-600">
                          {errors[technique.key]}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

