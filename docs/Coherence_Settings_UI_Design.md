# Coherence Settings UI Design

**Date:** 2025-11-14  
**Purpose:** Design UI for user-controlled coherence technique checklists

---

## UI Component Design

### Component: CoherenceSettingsPanel

**Location:** Dashboard page, below prompt input, above Generate button

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Advanced Coherence Settings                    [▼]      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ☑ Seed Control                                         │
│     Maintains consistent visual style across scenes     │
│     ⏱ No time impact | 💰 No cost impact                │
│                                                          │
│  ☑ Enhanced LLM Planning                                │
│     VideoDirectorGPT-style planning with consistency    │
│     ⏱ +5-10s | 💰 +$0.01                                │
│                                                          │
│  ☑ IP-Adapter (Character/Product Consistency)          │
│     Preserves identity across scenes                    │
│     ⏱ +10-15s | 💰 +$0.02                                │
│                                                          │
│  ☐ LoRA Training                                        │
│     Perfect consistency for recurring characters        │
│     ⏱ +30-60s | 💰 +$0.05 (requires trained LoRA)      │
│                                                          │
│  ☑ VBench Quality Control                               │
│     Automated quality assessment and regeneration       │
│     ⏱ +5-10s | 💰 No cost impact                        │
│                                                          │
│  ☑ Post-Processing Enhancement                          │
│     Brand-aware color grading and transitions           │
│     ⏱ +10-20s | 💰 No cost impact                       │
│                                                          │
│  ☐ ControlNet (Compositional Consistency)               │
│     Enforces scene layout and perspective               │
│     ⏱ +15-25s | 💰 +$0.03 (advanced)                    │
│                                                          │
│  ☐ CSFD Character Consistency Detection                 │
│     Measures character consistency across scenes        │
│     ⏱ +5s | 💰 No cost impact (character ads only)      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Detailed UI Specifications

### 1. Panel Structure

**Expandable Section:**
- Default: Collapsed (shows "Advanced Coherence Settings" with chevron)
- Click to expand/collapse
- Shows count of enabled techniques: "3 techniques enabled"
- Visual indicator when non-default settings are active

### 2. Each Technique Item

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│ ☑ Technique Name                              [ℹ️]       │
│    Description of what this technique does              │
│    ⏱ Time impact | 💰 Cost impact | 📊 Quality impact   │
└──────────────────────────────────────────────────────────┘
```

**Components:**
- **Checkbox/Toggle:** Enable/disable the technique
- **Technique Name:** Bold, clear label
- **Info Icon (ℹ️):** Tooltip with detailed explanation
- **Description:** Brief 1-2 sentence explanation
- **Impact Indicators:**
  - ⏱ Time: Estimated additional time (e.g., "+10-15s")
  - 💰 Cost: Estimated additional cost (e.g., "+$0.02")
  - 📊 Quality: Quality impact (e.g., "High", "Medium", "Low")

### 3. Default States

| Technique | Default | Reason |
|-----------|---------|--------|
| Seed Control | ☑ Enabled | Quick win, no cost, high impact |
| Enhanced LLM Planning | ☑ Enabled | Foundation for other techniques |
| IP-Adapter | ☑ Enabled (if entities) | High impact, moderate cost |
| LoRA Training | ☐ Disabled | Requires training, user must opt-in |
| VBench Quality Control | ☑ Enabled | Automated quality, no cost |
| Post-Processing Enhancement | ☑ Enabled | Improves final output, no cost |
| ControlNet | ☐ Disabled | Advanced, higher cost |
| CSFD Detection | ☐ Disabled | Character ads only, optional |

### 4. Dependencies and Validation

**Dependency Rules:**
- IP-Adapter requires Enhanced LLM Planning (to identify entities)
- LoRA requires Enhanced LLM Planning (to identify entities)
- ControlNet works best with Enhanced LLM Planning
- CSFD requires character consistency groups (from Enhanced Planning)

**Visual Indicators:**
- Disabled checkbox if dependency not met
- Warning icon if recommended combination not selected
- Info message explaining dependencies

### 5. Settings Persistence

**User Preferences:**
- Store in localStorage (optional)
- Remember last used settings
- "Reset to Defaults" button
- "Use Recommended" button (enables all recommended)

---

## React Component Structure

```typescript
interface CoherenceSettings {
  seedControl: boolean;
  enhancedPlanning: boolean;
  ipAdapter: boolean;
  lora: boolean;
  vbench: boolean;
  postProcessing: boolean;
  controlNet: boolean;
  csfd: boolean;
}

interface TechniqueInfo {
  id: keyof CoherenceSettings;
  name: string;
  description: string;
  defaultEnabled: boolean;
  timeImpact: string;
  costImpact: string;
  qualityImpact: "High" | "Medium" | "Low";
  dependencies?: string[];
  tooltip: string;
}
```

---

## API Integration

### Request Payload

```json
{
  "prompt": "Create a luxury watch ad",
  "coherence_settings": {
    "seed_control": true,
    "enhanced_planning": true,
    "ip_adapter": true,
    "lora": false,
    "vbench": true,
    "post_processing": true,
    "control_net": false,
    "csfd": false
  }
}
```

### Backend Schema

```python
# In Generation model
coherence_settings = Column(JSON, nullable=True)

# Example structure:
{
    "seed_control": True,
    "enhanced_planning": True,
    "ip_adapter": True,
    "lora": False,
    "vbench": True,
    "post_processing": True,
    "control_net": False,
    "csfd": False
}
```

---

## User Experience Flow

### Scenario 1: Default User (No Changes)
1. User enters prompt
2. Sees collapsed "Advanced Coherence Settings" section
3. Clicks Generate
4. System uses default settings (recommended techniques enabled)

### Scenario 2: Advanced User (Customizes Settings)
1. User enters prompt
2. Expands "Advanced Coherence Settings"
3. Reviews each technique
4. Enables/disables based on needs
5. Sees updated time/cost estimates
6. Clicks Generate
7. System applies only selected techniques

### Scenario 3: Character-Driven Ad
1. User enters prompt with character
2. System detects character entities
3. IP-Adapter checkbox auto-enables (with info message)
4. CSFD checkbox becomes available (was disabled)
5. User can enable CSFD for character consistency measurement

---

## Visual Design

### Color Coding

- **Enabled (Recommended):** Green checkmark, subtle green background
- **Enabled (User Selected):** Blue checkmark, subtle blue background
- **Disabled (Default):** Gray checkbox, normal background
- **Disabled (Dependency Missing):** Gray checkbox, red border, tooltip explaining dependency

### Icons

- ☑ Checkbox (enabled)
- ☐ Checkbox (disabled)
- ℹ️ Info icon (tooltip)
- ⚠️ Warning icon (dependency issue)
- ⏱ Time icon
- 💰 Cost icon
- 📊 Quality icon

---

## Implementation Notes

1. **Component Location:** Add to Dashboard.tsx below prompt input
2. **State Management:** Use React useState for settings
3. **Validation:** Check dependencies before submission
4. **API Integration:** Include settings in generation request
5. **Backend:** Add coherence_settings JSON field to Generation model
6. **Default Logic:** Apply defaults on component mount
7. **Persistence:** Optional localStorage for user preferences

---

_End of Design_

