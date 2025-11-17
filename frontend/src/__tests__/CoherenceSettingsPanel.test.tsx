/**
 * Unit tests for CoherenceSettingsPanel component.
 * Tests component rendering, expand/collapse, checkbox interactions, and validation.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CoherenceSettingsPanel, validateCoherenceSettings, getCoherenceWarnings } from "../components/coherence";
import type { CoherenceSettings } from "../components/coherence";

describe("CoherenceSettingsPanel", () => {
  const defaultSettings: CoherenceSettings = {
    seed_control: true,
    ip_adapter_reference: false,
    ip_adapter_sequential: false,
    lora: false,
    enhanced_planning: true,
    vbench_quality_control: true,
    automatic_regeneration: false,
    post_processing_enhancement: true,
    color_grading: false,
    controlnet: false,
    csfd_detection: false,
  };

  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render with default settings", () => {
    render(
      <CoherenceSettingsPanel
        settings={defaultSettings}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText("Advanced Coherence Settings")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /expand/i })).toBeInTheDocument();
  });

  it("should toggle expand/collapse correctly", () => {
    render(
      <CoherenceSettingsPanel
        settings={defaultSettings}
        onChange={mockOnChange}
      />
    );

    const expandButton = screen.getByRole("button", { name: /expand/i });
    
    // Initially collapsed - checkboxes should not be visible
    expect(screen.queryByLabelText(/seed control/i)).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(expandButton);
    expect(screen.getByLabelText(/seed control/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /collapse/i })).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(screen.getByRole("button", { name: /collapse/i }));
    expect(screen.queryByLabelText(/seed control/i)).not.toBeInTheDocument();
  });

  it("should display all coherence techniques when expanded", () => {
    render(
      <CoherenceSettingsPanel
        settings={defaultSettings}
        onChange={mockOnChange}
      />
    );

    // Expand panel
    fireEvent.click(screen.getByRole("button", { name: /expand/i }));

    // Check all techniques are displayed
    expect(screen.getByLabelText(/seed control/i)).toBeInTheDocument();
    // IP-Adapter appears multiple times (reference and sequential), so use getAllByLabelText
    expect(screen.getAllByLabelText(/ip-adapter/i).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/lora training/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/enhanced llm planning/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/vbench quality control/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/post-processing enhancement/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/controlnet/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/csfd/i)).toBeInTheDocument();
  });

  it("should update state when checkboxes are toggled", () => {
    render(
      <CoherenceSettingsPanel
        settings={defaultSettings}
        onChange={mockOnChange}
      />
    );

    // Expand panel
    fireEvent.click(screen.getByRole("button", { name: /expand/i }));

    // Toggle a checkbox (seed_control is the only implemented one, so test that)
    const seedControlCheckbox = screen.getByLabelText(/seed control/i);
    fireEvent.click(seedControlCheckbox);

    expect(mockOnChange).toHaveBeenCalledWith({
      ...defaultSettings,
      seed_control: false,
    });
  });

  it("should display descriptions for each technique", () => {
    render(
      <CoherenceSettingsPanel
        settings={defaultSettings}
        onChange={mockOnChange}
      />
    );

    // Expand panel
    fireEvent.click(screen.getByRole("button", { name: /expand/i }));

    // Check descriptions are present
    expect(screen.getByText(/ensures consistent visual style/i)).toBeInTheDocument();
    expect(screen.getByText(/uses the same real reference image/i)).toBeInTheDocument();
  });

  it("should display time and cost impact indicators", () => {
    render(
      <CoherenceSettingsPanel
        settings={defaultSettings}
        onChange={mockOnChange}
      />
    );

    // Expand panel
    fireEvent.click(screen.getByRole("button", { name: /expand/i }));

    // Check impact indicators are present (multiple techniques have these, so use getAllByText)
    expect(screen.getAllByText(/time:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/cost:/i).length).toBeGreaterThan(0);
  });

  it("should disable IP-Adapter when Enhanced Planning is disabled", () => {
    const settingsWithoutEnhancedPlanning: CoherenceSettings = {
      ...defaultSettings,
      enhanced_planning: false,
    };

    render(
      <CoherenceSettingsPanel
        settings={settingsWithoutEnhancedPlanning}
        onChange={mockOnChange}
      />
    );

    // Expand panel
    fireEvent.click(screen.getByRole("button", { name: /expand/i }));

    // IP-Adapter features are disabled (not implemented) and also require enhanced_planning
    const ipAdapterReferenceCheckbox = screen.getByLabelText(/ip-adapter.*reference images/i);
    expect(ipAdapterReferenceCheckbox).toBeDisabled();
    // "Coming soon" appears multiple times, so check that at least one exists
    expect(screen.getAllByText(/coming soon/i).length).toBeGreaterThan(0);
  });

  it("should display validation errors", () => {
    const errors = {
      ip_adapter_reference: "Requires Enhanced LLM Planning to be enabled",
    };

    render(
      <CoherenceSettingsPanel
        settings={defaultSettings}
        onChange={mockOnChange}
        errors={errors}
      />
    );

    // Expand panel
    fireEvent.click(screen.getByRole("button", { name: /expand/i }));

    expect(screen.getByText(/requires enhanced llm planning/i)).toBeInTheDocument();
  });

  it("should display warnings for recommended combinations", () => {
    const settingsWithDisabledRecommended: CoherenceSettings = {
      ...defaultSettings,
      seed_control: false, // Disabled recommended setting
      controlnet: true, // Enabled advanced setting
    };

    render(
      <CoherenceSettingsPanel
        settings={settingsWithDisabledRecommended}
        onChange={mockOnChange}
        showWarnings={true}
      />
    );

    // Expand panel
    fireEvent.click(screen.getByRole("button", { name: /expand/i }));

    // Check warnings are displayed
    expect(screen.getByText(/recommendations/i)).toBeInTheDocument();
    expect(screen.getByText(/recommended settings are disabled/i)).toBeInTheDocument();
    expect(screen.getByText(/advanced settings enabled/i)).toBeInTheDocument();
  });

  it("should not call onChange when disabled", () => {
    render(
      <CoherenceSettingsPanel
        settings={defaultSettings}
        onChange={mockOnChange}
        disabled={true}
      />
    );

    // Expand panel
    fireEvent.click(screen.getByRole("button", { name: /expand/i }));

    // Try to toggle checkbox (seed_control is the only implemented one)
    const seedControlCheckbox = screen.getByLabelText(/seed control/i);
    fireEvent.click(seedControlCheckbox);

    expect(mockOnChange).not.toHaveBeenCalled();
  });
});

describe("validateCoherenceSettings", () => {
  it("should return no errors for valid settings", () => {
    const settings: CoherenceSettings = {
      seed_control: true,
      ip_adapter_reference: true,
      ip_adapter_sequential: false,
      lora: false,
      enhanced_planning: true, // Required for IP-Adapter
      vbench_quality_control: true,
      automatic_regeneration: false,
      post_processing_enhancement: true,
      color_grading: false,
      controlnet: false,
      csfd_detection: false,
    };

    const errors = validateCoherenceSettings(settings);
    expect(Object.keys(errors)).toHaveLength(0);
  });

  it("should return error when IP-Adapter is enabled without Enhanced Planning", () => {
    const settings: CoherenceSettings = {
      seed_control: true,
      ip_adapter_reference: true,
      ip_adapter_sequential: false,
      lora: false,
      enhanced_planning: false, // Missing requirement
      vbench_quality_control: true,
      automatic_regeneration: false,
      post_processing_enhancement: true,
      color_grading: false,
      controlnet: false,
      csfd_detection: false,
    };

    const errors = validateCoherenceSettings(settings);
    expect(errors.ip_adapter_reference).toContain("Requires");
    expect(errors.ip_adapter_reference).toContain("Enhanced LLM Planning");
  });

  it("should return error when both IP-Adapter modes are enabled", () => {
    const settings: CoherenceSettings = {
      seed_control: true,
      ip_adapter_reference: true,
      ip_adapter_sequential: true, // Incompatible with reference mode
      lora: false,
      enhanced_planning: true,
      vbench_quality_control: true,
      automatic_regeneration: false,
      post_processing_enhancement: true,
      color_grading: false,
      controlnet: false,
      csfd_detection: false,
    };

    const errors = validateCoherenceSettings(settings);
    expect(errors.ip_adapter_reference || errors.ip_adapter_sequential).toBeDefined();
  });
});

describe("getCoherenceWarnings", () => {
  it("should return warnings when recommended settings are disabled", () => {
    const settings: CoherenceSettings = {
      seed_control: false, // Disabled recommended
      ip_adapter_reference: false,
      ip_adapter_sequential: false,
      lora: false,
      enhanced_planning: false, // Disabled recommended
      vbench_quality_control: true,
      automatic_regeneration: false,
      post_processing_enhancement: true,
      color_grading: false,
      controlnet: false,
      csfd_detection: false,
    };

    const warnings = getCoherenceWarnings(settings);
    expect(warnings.length).toBeGreaterThan(0);
    expect(warnings.some(w => w.includes("Recommended settings are disabled"))).toBe(true);
  });

  it("should return warnings when advanced settings are enabled", () => {
    const settings: CoherenceSettings = {
      seed_control: true,
      ip_adapter_reference: false,
      ip_adapter_sequential: false,
      lora: true, // Advanced setting enabled
      enhanced_planning: true,
      vbench_quality_control: true,
      automatic_regeneration: false,
      post_processing_enhancement: true,
      color_grading: false,
      controlnet: true, // Advanced setting enabled
      csfd_detection: false,
    };

    const warnings = getCoherenceWarnings(settings);
    expect(warnings.length).toBeGreaterThan(0);
    expect(warnings.some(w => w.includes("Advanced settings enabled"))).toBe(true);
  });

  it("should return no warnings for default recommended settings", () => {
    const settings: CoherenceSettings = {
      seed_control: true,
      ip_adapter_reference: false,
      ip_adapter_sequential: false,
      lora: false,
      enhanced_planning: true,
      vbench_quality_control: true,
      automatic_regeneration: false,
      post_processing_enhancement: true,
      color_grading: false,
      controlnet: false,
      csfd_detection: false,
    };

    const warnings = getCoherenceWarnings(settings);
    expect(warnings.length).toBe(0);
  });
});

