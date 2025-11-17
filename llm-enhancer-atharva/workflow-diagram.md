# LLM Enhancer Workflow - Mermaid Diagram

## Complete Workflow Visualization

```mermaid
flowchart TD
    Start([User Prompt + Optional Reference Image]) --> LLM[Storyboard Planner<br/>GPT-4o]
    
    LLM --> Storyboard[Storyboard Plan]
    Storyboard --> |4 Detailed Prompts<br/>40-80 words each| Scene1[Scene 1: Attention]
    Storyboard --> |Consistency Markers| Scene2[Scene 2: Interest]
    Storyboard --> |Scene Descriptions| Scene3[Scene 3: Desire]
    Storyboard --> |Start/End Prompts| Scene4[Scene 4: Action]
    
    Scene1 --> Img1[Image Generation 1<br/>Nano Banana<br/>No Reference]
    Scene2 --> Img2[Image Generation 2<br/>Nano Banana<br/>Ref: Image 1]
    Scene3 --> Img3[Image Generation 3<br/>Nano Banana<br/>Ref: Image 2]
    Scene4 --> Img4[Image Generation 4<br/>Nano Banana<br/>Ref: Image 3]
    
    Img1 --> |Sequential| Img2
    Img2 --> |Sequential| Img3
    Img3 --> |Sequential| Img4
    
    Img1 --> |Reference Image 1| Vid1[Video Generation 1<br/>Sora-2/Veo-3/PixVerse]
    Img2 --> |Reference Image 2| Vid2[Video Generation 2<br/>Sora-2/Veo-3/PixVerse]
    Img3 --> |Reference Image 3| Vid3[Video Generation 3<br/>Sora-2/Veo-3/PixVerse]
    Img4 --> |Reference Image 4| Vid4[Video Generation 4<br/>Sora-2/Veo-3/PixVerse]
    
    Storyboard --> |Detailed Prompts| Vid1
    Storyboard --> |Detailed Prompts| Vid2
    Storyboard --> |Detailed Prompts| Vid3
    Storyboard --> |Detailed Prompts| Vid4
    
    Storyboard --> |Consistency Markers| Vid1
    Storyboard --> |Consistency Markers| Vid2
    Storyboard --> |Consistency Markers| Vid3
    Storyboard --> |Consistency Markers| Vid4
    
    Vid1 --> |Parallel Generation| Assembly[Video Assembly]
    Vid2 --> |Parallel Generation| Assembly
    Vid3 --> |Parallel Generation| Assembly
    Vid4 --> |Parallel Generation| Assembly
    
    Assembly --> Overlay[Add Text Overlays]
    Overlay --> Audio[Add Voiceover & Music]
    Audio --> Brand[Add Brand Overlay]
    Brand --> Final([Final 16-Second Video])
    
    style Start fill:#e1f5ff
    style LLM fill:#fff4e1
    style Storyboard fill:#fff4e1
    style Img1 fill:#e8f5e9
    style Img2 fill:#e8f5e9
    style Img3 fill:#e8f5e9
    style Img4 fill:#e8f5e9
    style Vid1 fill:#f3e5f5
    style Vid2 fill:#f3e5f5
    style Vid3 fill:#f3e5f5
    style Vid4 fill:#f3e5f5
    style Assembly fill:#e3f2fd
    style Final fill:#c8e6c9
```

## Detailed Phase Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant StoryboardPlanner as Storyboard Planner<br/>(GPT-4o)
    participant ImageGen as Image Generation<br/>(Nano Banana)
    participant VideoGen as Video Generation<br/>(Sora-2/Veo-3/PixVerse)
    participant Assembly as Video Assembly
    
    User->>API: POST /api/generate<br/>{prompt, use_llm: true}
    
    Note over API,StoryboardPlanner: Phase 1: Storyboard Planning
    API->>StoryboardPlanner: User prompt + optional reference image
    StoryboardPlanner->>StoryboardPlanner: Generate 4 detailed prompts<br/>(40-80 words each)
    StoryboardPlanner->>StoryboardPlanner: Generate consistency markers<br/>(style, color, lighting, mood)
    StoryboardPlanner->>StoryboardPlanner: Generate scene descriptions<br/>(AIDA framework)
    StoryboardPlanner->>API: Storyboard plan with 4 scenes
    
    Note over API,ImageGen: Phase 2: Sequential Image Generation
    API->>ImageGen: Scene 1 prompt + markers
    ImageGen->>ImageGen: Generate Image 1 (no reference)
    ImageGen->>API: Image 1 path
    
    API->>ImageGen: Scene 2 prompt + markers + Image 1 ref
    ImageGen->>ImageGen: Generate Image 2 (ref: Image 1)
    ImageGen->>API: Image 2 path
    
    API->>ImageGen: Scene 3 prompt + markers + Image 2 ref
    ImageGen->>ImageGen: Generate Image 3 (ref: Image 2)
    ImageGen->>API: Image 3 path
    
    API->>ImageGen: Scene 4 prompt + markers + Image 3 ref
    ImageGen->>ImageGen: Generate Image 4 (ref: Image 3)
    ImageGen->>API: Image 4 path
    
    Note over API,VideoGen: Phase 3: Parallel Video Generation
    par Parallel Generation
        API->>VideoGen: Scene 1: Prompt + Markers + Image 1
        VideoGen->>API: Video 1 clip
    and
        API->>VideoGen: Scene 2: Prompt + Markers + Image 2
        VideoGen->>API: Video 2 clip
    and
        API->>VideoGen: Scene 3: Prompt + Markers + Image 3
        VideoGen->>API: Video 3 clip
    and
        API->>VideoGen: Scene 4: Prompt + Markers + Image 4
        VideoGen->>API: Video 4 clip
    end
    
    Note over API,Assembly: Phase 4: Video Assembly
    API->>Assembly: All 4 video clips
    Assembly->>Assembly: Combine clips sequentially
    Assembly->>Assembly: Add text overlays
    Assembly->>Assembly: Add voiceover & music
    Assembly->>Assembly: Add brand overlay
    Assembly->>API: Final 16-second video
    API->>User: Generation complete
```

## Kling 2.5 Turbo Pro Workflow (with Start/End Frames)

```mermaid
flowchart TD
    Start([User Prompt]) --> LLM[Storyboard Planner<br/>GPT-4o]
    
    LLM --> Storyboard[Storyboard Plan]
    Storyboard --> |4 Scenes| Scene[Scene Processing]
    
    Scene --> |For each scene| ImgGen[Image Generation<br/>Nano Banana]
    
    ImgGen --> RefImg[Reference Image]
    ImgGen --> StartImg[Start Image<br/>First Frame]
    ImgGen --> EndImg[End Image<br/>Last Frame]
    
    RefImg --> Kling[Kling 2.5 Turbo Pro<br/>Video Generation]
    StartImg --> Kling
    EndImg --> Kling
    Storyboard --> |Detailed Prompt| Kling
    Storyboard --> |Consistency Markers| Kling
    
    Kling --> Video[Generated Video Clip<br/>Precise Frame Control]
    
    Video --> Assembly[Video Assembly]
    Assembly --> Final([Final Video])
    
    style Start fill:#e1f5ff
    style LLM fill:#fff4e1
    style ImgGen fill:#e8f5e9
    style RefImg fill:#c8e6c9
    style StartImg fill:#c8e6c9
    style EndImg fill:#c8e6c9
    style Kling fill:#f3e5f5
    style Video fill:#f3e5f5
    style Final fill:#c8e6c9
```

## Data Flow Architecture

```mermaid
graph TB
    subgraph "Input Layer"
        UserPrompt[User Prompt]
        RefImage[Optional Reference Image]
    end
    
    subgraph "Planning Layer"
        StoryboardPlanner[Storyboard Planner<br/>GPT-4o]
        StoryboardPlan[Storyboard Plan<br/>JSON]
    end
    
    subgraph "Image Generation Layer"
        ImgGen1[Image Gen 1<br/>No Ref]
        ImgGen2[Image Gen 2<br/>Ref: Img1]
        ImgGen3[Image Gen 3<br/>Ref: Img2]
        ImgGen4[Image Gen 4<br/>Ref: Img3]
    end
    
    subgraph "Video Generation Layer"
        VidGen1[Video Gen 1<br/>Prompt + Img1]
        VidGen2[Video Gen 2<br/>Prompt + Img2]
        VidGen3[Video Gen 3<br/>Prompt + Img3]
        VidGen4[Video Gen 4<br/>Prompt + Img4]
    end
    
    subgraph "Assembly Layer"
        Stitcher[Video Stitcher]
        OverlayEngine[Text Overlay Engine]
        AudioEngine[Audio Engine]
        BrandEngine[Brand Overlay Engine]
    end
    
    subgraph "Output Layer"
        FinalVideo[Final 16s Video]
    end
    
    UserPrompt --> StoryboardPlanner
    RefImage --> StoryboardPlanner
    StoryboardPlanner --> StoryboardPlan
    
    StoryboardPlan --> ImgGen1
    StoryboardPlan --> ImgGen2
    StoryboardPlan --> ImgGen3
    StoryboardPlan --> ImgGen4
    
    ImgGen1 --> ImgGen2
    ImgGen2 --> ImgGen3
    ImgGen3 --> ImgGen4
    
    StoryboardPlan --> VidGen1
    StoryboardPlan --> VidGen2
    StoryboardPlan --> VidGen3
    StoryboardPlan --> VidGen4
    
    ImgGen1 --> VidGen1
    ImgGen2 --> VidGen2
    ImgGen3 --> VidGen3
    ImgGen4 --> VidGen4
    
    VidGen1 --> Stitcher
    VidGen2 --> Stitcher
    VidGen3 --> Stitcher
    VidGen4 --> Stitcher
    
    Stitcher --> OverlayEngine
    OverlayEngine --> AudioEngine
    AudioEngine --> BrandEngine
    BrandEngine --> FinalVideo
    
    style UserPrompt fill:#e1f5ff
    style StoryboardPlanner fill:#fff4e1
    style ImgGen1 fill:#e8f5e9
    style ImgGen2 fill:#e8f5e9
    style ImgGen3 fill:#e8f5e9
    style ImgGen4 fill:#e8f5e9
    style VidGen1 fill:#f3e5f5
    style VidGen2 fill:#f3e5f5
    style VidGen3 fill:#f3e5f5
    style VidGen4 fill:#f3e5f5
    style FinalVideo fill:#c8e6c9
```

## Consistency System Flow

```mermaid
flowchart LR
    UserPrompt[User Prompt] --> LLM[GPT-4o]
    LLM --> Markers[Consistency Markers<br/>Style, Color, Lighting, Mood]
    
    Markers --> Img1[Image 1]
    Markers --> Img2[Image 2]
    Markers --> Img3[Image 3]
    Markers --> Img4[Image 4]
    
    Img1 -.->|Visual Reference| Img2
    Img2 -.->|Visual Reference| Img3
    Img3 -.->|Visual Reference| Img4
    
    Markers --> Vid1[Video 1]
    Markers --> Vid2[Video 2]
    Markers --> Vid3[Video 3]
    Markers --> Vid4[Video 4]
    
    Img1 --> Vid1
    Img2 --> Vid2
    Img3 --> Vid3
    Img4 --> Vid4
    
    style Markers fill:#fff4e1
    style Img1 fill:#e8f5e9
    style Img2 fill:#e8f5e9
    style Img3 fill:#e8f5e9
    style Img4 fill:#e8f5e9
    style Vid1 fill:#f3e5f5
    style Vid2 fill:#f3e5f5
    style Vid3 fill:#f3e5f5
    style Vid4 fill:#f3e5f5
```

