/**
 * ParallelGenerationPanel component for parallel video generation and comparison.
 * Allows users to generate multiple variations in parallel for comparison.
 */
import React, { useState, useEffect } from "react";
import { Button } from "../ui/Button";
import { Textarea } from "../ui/Textarea";
import { Select } from "../ui/Select";
import { ErrorMessage } from "../ui/ErrorMessage";
import { CoherenceSettingsPanel, validateCoherenceSettings } from "../coherence";
import type { CoherenceSettings as CoherenceSettingsType } from "../coherence";
import type { GenerateRequest } from "../../lib/generationService";

export type ComparisonType = "settings" | "prompt";

export interface ParallelGenerationPanelProps {
  onSubmit: (variations: GenerateRequest[], comparisonType: ComparisonType) => void;
  onCancel?: () => void;
  isLoading?: boolean;
  error?: string;
}

const MIN_VARIATIONS = 2;
const MAX_VARIATIONS = 10;
const MIN_PROMPT_LENGTH = 10;
const MAX_PROMPT_LENGTH = 500;

/**
 * Default coherence settings for new profiles.
 */
const getDefaultCoherenceSettings = (): CoherenceSettingsType => ({
  seed_control: true,
  ip_adapter_reference: false,
  ip_adapter_sequential: false,
  lora: false,
  enhanced_planning: true,
  vbench_quality_control: true,
  post_processing_enhancement: true,
  controlnet: false,
  csfd_detection: false,
});

/**
 * ParallelGenerationPanel component.
 */
export const ParallelGenerationPanel: React.FC<ParallelGenerationPanelProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  error,
}) => {
  const [comparisonType, setComparisonType] = useState<ComparisonType>("settings");
  const [variationCount, setVariationCount] = useState<number>(2);
  
  // Settings comparison mode: single prompt, multiple setting profiles
  const [settingsPrompt, setSettingsPrompt] = useState<string>("");
  const [settingsTitle, setSettingsTitle] = useState<string>(""); // Optional title for settings comparison
  const [settingsProfiles, setSettingsProfiles] = useState<CoherenceSettingsType[]>([
    getDefaultCoherenceSettings(),
    getDefaultCoherenceSettings(),
  ]);
  
  // Prompt comparison mode: multiple prompts, single settings
  const [promptVariations, setPromptVariations] = useState<string[]>(["", ""]);
  const [promptTitles, setPromptTitles] = useState<string[]>(["", ""]); // Titles for each prompt variation
  const [promptSettings, setPromptSettings] = useState<CoherenceSettingsType>(getDefaultCoherenceSettings());
  
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  /**
   * Update settings profiles when variation count changes (settings comparison mode).
   */
  useEffect(() => {
    if (comparisonType === "settings") {
      const currentCount = settingsProfiles.length;
      if (variationCount > currentCount) {
        // Add new profiles with default settings
        const newProfiles = Array.from({ length: variationCount - currentCount }, () =>
          getDefaultCoherenceSettings()
        );
        setSettingsProfiles([...settingsProfiles, ...newProfiles]);
      } else if (variationCount < currentCount) {
        // Remove excess profiles
        setSettingsProfiles(settingsProfiles.slice(0, variationCount));
      }
    }
  }, [variationCount, comparisonType]);

  /**
   * Update prompt variations when variation count changes (prompt comparison mode).
   */
  useEffect(() => {
    if (comparisonType === "prompt") {
      const currentCount = promptVariations.length;
      if (variationCount > currentCount) {
        // Add new empty prompts and titles
        const newPrompts = Array.from({ length: variationCount - currentCount }, () => "");
        const newTitles = Array.from({ length: variationCount - currentCount }, () => "");
        setPromptVariations([...promptVariations, ...newPrompts]);
        setPromptTitles([...promptTitles, ...newTitles]);
      } else if (variationCount < currentCount) {
        // Remove excess prompts and titles
        setPromptVariations(promptVariations.slice(0, variationCount));
        setPromptTitles(promptTitles.slice(0, variationCount));
      }
    }
  }, [variationCount, comparisonType]);

  /**
   * Validate form inputs.
   */
  const validate = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (comparisonType === "settings") {
      // Validate single prompt
      if (!settingsPrompt || settingsPrompt.length < MIN_PROMPT_LENGTH || settingsPrompt.length > MAX_PROMPT_LENGTH) {
        newErrors.settingsPrompt = `Prompt must be between ${MIN_PROMPT_LENGTH} and ${MAX_PROMPT_LENGTH} characters`;
      }

      // Validate each settings profile
      settingsProfiles.forEach((profile, index) => {
        const profileErrors = validateCoherenceSettings(profile);
        if (Object.keys(profileErrors).length > 0) {
          newErrors[`profile_${index}`] = `Profile ${String.fromCharCode(65 + index)} has invalid settings`;
        }
      });
    } else {
      // Validate all prompts
      promptVariations.forEach((prompt, index) => {
        if (!prompt || prompt.length < MIN_PROMPT_LENGTH || prompt.length > MAX_PROMPT_LENGTH) {
          newErrors[`prompt_${index}`] = `Prompt ${index + 1} must be between ${MIN_PROMPT_LENGTH} and ${MAX_PROMPT_LENGTH} characters`;
        }
      });

      // Validate single settings
      const settingsErrors = validateCoherenceSettings(promptSettings);
      if (Object.keys(settingsErrors).length > 0) {
        newErrors.promptSettings = "Coherence settings are invalid";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    let variations: GenerateRequest[] = [];

    if (comparisonType === "settings") {
      // Create variations with same prompt, different settings
      // Use variation letter as title if no title provided
      variations = settingsProfiles.map((profile, index) => {
        const variationLetter = String.fromCharCode(65 + index); // A, B, C, etc.
        const variationTitle = settingsTitle 
          ? `${settingsTitle} - ${variationLetter}`
          : `Variation ${variationLetter}`;
        return {
          prompt: settingsPrompt,
          title: variationTitle,
          coherence_settings: profile,
        };
      });
    } else {
      // Create variations with different prompts, same settings
      variations = promptVariations.map((prompt, index) => {
        const variationLetter = String.fromCharCode(65 + index); // A, B, C, etc.
        const variationTitle = promptTitles[index] || `Variation ${variationLetter}`;
        return {
          prompt,
          title: variationTitle,
          coherence_settings: promptSettings,
        };
      });
    }

    onSubmit(variations, comparisonType);
  };

  /**
   * Update settings profile at index.
   */
  const updateSettingsProfile = (index: number, settings: CoherenceSettingsType) => {
    const newProfiles = [...settingsProfiles];
    newProfiles[index] = settings;
    setSettingsProfiles(newProfiles);
  };

  /**
   * Update prompt variation at index.
   */
  const updatePromptVariation = (index: number, prompt: string) => {
    const newPrompts = [...promptVariations];
    newPrompts[index] = prompt;
    setPromptVariations(newPrompts);
  };

  /**
   * Update prompt title at index.
   */
  const updatePromptTitle = (index: number, title: string) => {
    const newTitles = [...promptTitles];
    newTitles[index] = title;
    setPromptTitles(newTitles);
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        Parallel Generation Mode
      </h2>
      <p className="text-gray-600 mb-6">
        Generate multiple video variations in parallel to compare different settings or prompts.
      </p>

      {error && <ErrorMessage message={error} className="mb-4" />}

      <form onSubmit={handleSubmit}>
        {/* Comparison Type Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Comparison Mode
          </label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="comparisonType"
                value="settings"
                checked={comparisonType === "settings"}
                onChange={(e) => setComparisonType(e.target.value as ComparisonType)}
                className="mr-2"
                disabled={isLoading}
              />
              <span className="text-sm text-gray-700">Settings Comparison</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="comparisonType"
                value="prompt"
                checked={comparisonType === "prompt"}
                onChange={(e) => setComparisonType(e.target.value as ComparisonType)}
                className="mr-2"
                disabled={isLoading}
              />
              <span className="text-sm text-gray-700">Prompt Comparison</span>
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {comparisonType === "settings"
              ? "Same prompt, different coherence settings"
              : "Different prompts, same coherence settings"}
          </p>
        </div>

        {/* Variation Count Selector */}
        <div className="mb-6">
          <Select
            label="Number of Variations"
            value={variationCount.toString()}
            onChange={(e) => setVariationCount(parseInt(e.target.value, 10))}
            disabled={isLoading}
            options={Array.from({ length: MAX_VARIATIONS - MIN_VARIATIONS + 1 }, (_, i) => ({
              value: (MIN_VARIATIONS + i).toString(),
              label: `${MIN_VARIATIONS + i} variations`,
            }))}
          />
        </div>

        {/* Settings Comparison Mode */}
        {comparisonType === "settings" && (
          <div className="space-y-6">
            {/* Optional Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Group Title (Optional)
              </label>
              <input
                type="text"
                value={settingsTitle}
                onChange={(e) => setSettingsTitle(e.target.value)}
                placeholder="e.g., Coffee Maker Ad Comparison"
                maxLength={200}
                disabled={isLoading}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <p className="mt-1 text-xs text-gray-500">
                Videos will be named: "[Title] - A", "[Title] - B", etc.
              </p>
            </div>

            {/* Single Prompt */}
            <div>
              <Textarea
                label="Prompt (shared across all variations)"
                value={settingsPrompt}
                onChange={(e) => setSettingsPrompt(e.target.value)}
                placeholder="Enter your prompt here..."
                rows={4}
                disabled={isLoading}
                className={errors.settingsPrompt ? "border-red-500" : ""}
              />
              {errors.settingsPrompt && (
                <ErrorMessage message={errors.settingsPrompt} className="mt-1" />
              )}
            </div>

            {/* Multiple Settings Profiles */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                Settings Profiles
              </label>
              <div className="space-y-4">
                {settingsProfiles.map((profile, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-800 mb-3">
                      Profile {String.fromCharCode(65 + index)}
                    </h3>
                    <CoherenceSettingsPanel
                      settings={profile}
                      onChange={(settings) => updateSettingsProfile(index, settings)}
                      errors={errors[`profile_${index}`] ? { [errors[`profile_${index}`]]: errors[`profile_${index}`] } : {}}
                      disabled={isLoading}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Prompt Comparison Mode */}
        {comparisonType === "prompt" && (
          <div className="space-y-6">
            {/* Multiple Prompts */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                Prompt Variations
              </label>
              <div className="space-y-4">
                {promptVariations.map((prompt, index) => (
                  <div key={index} className="space-y-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Title (Optional) - {String.fromCharCode(65 + index)}
                      </label>
                      <input
                        type="text"
                        value={promptTitles[index] || ""}
                        onChange={(e) => updatePromptTitle(index, e.target.value)}
                        placeholder={`Variation ${String.fromCharCode(65 + index)}`}
                        maxLength={200}
                        disabled={isLoading}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Prompt {String.fromCharCode(65 + index)}
                      </label>
                      <Textarea
                        value={prompt}
                        onChange={(e) => updatePromptVariation(index, e.target.value)}
                        placeholder={`Enter prompt variation ${String.fromCharCode(65 + index)}...`}
                        rows={3}
                        disabled={isLoading}
                        className={errors[`prompt_${index}`] ? "border-red-500" : ""}
                      />
                      {errors[`prompt_${index}`] && (
                        <ErrorMessage message={errors[`prompt_${index}`]} className="mt-1" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Single Settings Panel */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                Coherence Settings (shared across all prompts)
              </label>
              <CoherenceSettingsPanel
                settings={promptSettings}
                onChange={setPromptSettings}
                errors={errors.promptSettings ? { [errors.promptSettings]: errors.promptSettings } : {}}
                disabled={isLoading}
              />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex gap-4">
          <Button
            type="submit"
            disabled={isLoading}
            className="flex-1"
          >
            {isLoading ? "Starting Generation..." : `Generate ${variationCount} Variations`}
          </Button>
          {onCancel && (
            <Button
              type="button"
              variant="secondary"
              onClick={onCancel}
              disabled={isLoading}
            >
              Cancel
            </Button>
          )}
        </div>

        {/* Estimated Cost Note */}
        <p className="text-xs text-gray-500 mt-4">
          Note: Generating {variationCount} variations will cost approximately {variationCount}x the cost of a single generation.
        </p>
      </form>
    </div>
  );
};

