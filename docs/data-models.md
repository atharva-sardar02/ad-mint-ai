# Data Models - Ad Mint AI

**Generated:** 2025-11-22
**Database:** SQLAlchemy ORM (SQLite dev, PostgreSQL prod)

---

## Overview

Ad Mint AI uses SQLAlchemy 2.0+ for database operations with support for both SQLite (development) and PostgreSQL (production). The schema tracks users, video generations, brand assets, and quality metrics.

---

## Core Models

### User

User authentication and profile.

**Table:** `users`

```python
class User(Base):
    id: str (UUID, PK)
    username: str (unique, indexed)
    email: str (unique, indexed)
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime

    # Relationships
    generations: List[Generation]
    generation_groups: List[GenerationGroup]
    editing_sessions: List[EditingSession]
    brand_styles: List[BrandStyle]
    product_images: List[ProductImage]
```

**Indexes:**
- `username` (unique)
- `email` (unique)

---

### Generation

Primary model for video generation jobs across all pipelines.

**Table:** `generations`

```python
class Generation(Base):
    # Primary Key
    id: str (UUID, PK)
    user_id: str (FK → users.id, indexed)

    # Basic Info
    title: str | None (max 200 chars)
    prompt: str (required)
    duration: int = 15 (seconds)
    aspect_ratio: str = "9:16"

    # Status Tracking
    status: str = "pending" (indexed)
        # Values: "pending", "processing", "completed", "failed"
    progress: int = 0 (0-100)
    current_step: str | None (max 100 chars)

    # Output Paths
    video_path: str | None (max 500 chars, local filesystem path)
    video_url: str | None (max 500 chars, URL for frontend)
    thumbnail_url: str | None (max 500 chars)
    temp_clip_paths: JSON | None (array of scene video paths)

    # Generation Parameters
    framework: str | None (max 20 chars)
        # Values: "PAS", "BAB", "AIDA", "master_mode"
    model: str | None (max 100 chars)
        # E.g., "openai/sora-2", "kling-v1.5", "runway-gen3"
    num_scenes: int | None
    num_clips: int | None
    use_llm: bool = True

    # LLM & Planning Data (JSON)
    llm_specification: JSON | None
        # Structure: AdSpecification schema from LLM
    scene_plan: JSON | None
        # Structure: ScenePlan with scene breakdowns
    llm_conversation_history: JSON | None
        # Master mode agent conversations
        # Array of {role, iteration, content, timestamp}

    # Visual Consistency Settings (JSON)
    coherence_settings: JSON | None
        # Structure: {
        #   use_seed_control: bool,
        #   use_latent_reuse: bool,
        #   use_ip_adapter: bool,
        #   seed_value: int | None
        # }
    seed_value: int | None (for reproducibility)

    # Execution Metadata
    generation_time_seconds: int | None
    cost: float | None (USD)
    error_message: str | None
    cancellation_requested: bool = False

    # Relationships & Versioning
    generation_group_id: str | None (FK → generation_groups.id, indexed)
    parent_generation_id: str | None (FK → generations.id, indexed, self-referential)

    # Timestamps
    created_at: datetime (indexed)
    completed_at: datetime | None

    # Relationships
    user: User
    generation_group: GenerationGroup
    parent_generation: Generation (for edited versions)
    edited_versions: List[Generation] (backref)
    quality_metrics: List[QualityMetric]
```

**Indexes:**
- `user_id`
- `status`
- `generation_group_id`
- `parent_generation_id`
- `created_at`

**Key JSON Fields:**

**llm_specification:**
```json
{
  "hook": "...",
  "problem": "...",
  "agitation": "...",
  "solution": "...",
  "call_to_action": "..."
}
```

**scene_plan:**
```json
{
  "total_scenes": 3,
  "cohesion_score": 85,
  "scenes": [
    {
      "scene_number": 1,
      "content": "...",
      "duration": 5,
      "visual_elements": ["..."]
    }
  ]
}
```

**llm_conversation_history:** (Master Mode)
```json
[
  {
    "role": "director",
    "iteration": 1,
    "content": "Initial story draft...",
    "timestamp": "2025-11-22T12:00:00Z"
  },
  {
    "role": "critic",
    "iteration": 1,
    "content": "Critique with score and feedback...",
    "timestamp": "2025-11-22T12:01:00Z"
  }
]
```

---

### GenerationGroup

Groups related generations for A/B testing and parallel comparisons.

**Table:** `generation_groups`

```python
class GenerationGroup(Base):
    id: str (UUID, PK)
    user_id: str (FK → users.id, indexed)
    created_at: datetime (indexed)
    comparison_type: Enum["settings", "prompt"]
        # "settings" - comparing coherence settings
        # "prompt" - comparing prompt variations

    # Relationships
    user: User
    generations: List[Generation]
```

**Indexes:**
- `user_id`
- `created_at`

**Use Cases:**
- Test different seed values for same prompt
- Compare PAS vs AIDA frameworks
- A/B test prompt variations

---

### QualityMetric

Stores quality scoring metrics for images and videos.

**Table:** `quality_metrics`

```python
class QualityMetric(Base):
    id: str (UUID, PK)
    generation_id: str (FK → generations.id, indexed)
    scene_number: int | None (null for overall video metrics)
    metric_name: str (indexed)
        # Values: "image_quality", "temporal_consistency",
        #         "subject_consistency", "aesthetic_quality", etc.
    metric_value: float
    model_name: str | None
        # E.g., "vbench", "clip", "aesthetic_predictor"
    created_at: datetime

    # Relationships
    generation: Generation
```

**Indexes:**
- `generation_id`
- `metric_name`

**Common Metrics:**
- `image_quality` - Overall image quality score (0-100)
- `aesthetic_quality` - Aesthetic appeal score
- `temporal_consistency` - Frame-to-frame consistency
- `subject_consistency` - Character/object consistency across scenes
- `motion_smoothness` - Motion quality
- `dynamic_range` - Color and contrast quality

---

## Brand & Product Models

### BrandStyle

Stores extracted brand style information from uploaded images.

**Table:** `brand_styles`

```python
class BrandStyle(Base):
    id: str (UUID, PK)
    user_id: str (FK → users.id, indexed)
    name: str (max 200 chars)
    description: str | None

    # Extracted Style Data (JSON)
    style_data: JSON
        # Structure: {
        #   "color_palette": ["#FF5733", "#33FF57"],
        #   "visual_theme": "minimalist modern",
        #   "typography_style": "sans-serif bold",
        #   "mood": "energetic",
        #   "lighting_preference": "bright natural"
        # }

    # Source Images
    image_folder_path: str | None (max 500 chars)
    sample_images: JSON | None (array of image paths)

    created_at: datetime (indexed)
    updated_at: datetime

    # Relationships
    user: User
```

**Indexes:**
- `user_id`
- `created_at`

**style_data Structure:**
```json
{
  "color_palette": ["#1A1A1A", "#FFFFFF", "#FF6B35"],
  "visual_theme": "minimalist modern with bold accents",
  "typography_style": "sans-serif geometric fonts",
  "mood": "professional yet approachable",
  "lighting_preference": "soft directional lighting",
  "composition_style": "rule of thirds, negative space",
  "brand_keywords": ["sustainable", "innovative", "accessible"]
}
```

---

### ProductImage

Stores user-uploaded product images for use in video generation.

**Table:** `product_images`

```python
class ProductImage(Base):
    id: str (UUID, PK)
    user_id: str (FK → users.id, indexed)
    name: str (max 200 chars)
    description: str | None

    # File Info
    image_path: str (max 500 chars, local filesystem)
    image_url: str (max 500 chars, URL for frontend)
    file_size_bytes: int
    image_width: int
    image_height: int
    mime_type: str (max 50 chars)

    # Categorization
    category: str | None (max 100 chars)
        # E.g., "product-shot", "lifestyle", "detail", "packaging"
    tags: JSON | None (array of strings)

    created_at: datetime (indexed)

    # Relationships
    user: User
```

**Indexes:**
- `user_id`
- `created_at`

---

### EditingSession

Tracks video editing sessions (for video editor feature).

**Table:** `editing_sessions`

```python
class EditingSession(Base):
    id: str (UUID, PK)
    generation_id: str (FK → generations.id)
    user_id: str (FK → users.id, indexed)

    # Edit Data (JSON)
    edit_data: JSON
        # Structure: {
        #   "clips": [{id, start, end, position, ...}],
        #   "transitions": [...],
        #   "effects": [...]
        # }

    # Output
    edited_video_path: str | None (max 500 chars)
    edited_video_url: str | None (max 500 chars)

    status: str = "draft"
        # Values: "draft", "rendering", "completed", "failed"

    created_at: datetime (indexed)
    updated_at: datetime

    # Relationships
    generation: Generation
    user: User
```

**Indexes:**
- `user_id`
- `created_at`

---

## Relationships Diagram

```
User
├── generations (1:many)
│   ├── quality_metrics (1:many)
│   ├── parent_generation (self-referential)
│   └── edited_versions (self-referential backref)
├── generation_groups (1:many)
│   └── generations (1:many)
├── editing_sessions (1:many)
├── brand_styles (1:many)
└── product_images (1:many)
```

---

## Database Migrations

**Migration System:** Alembic (via custom scripts)

**Location:** `backend/app/db/migrations/`

### Migration Files

- `add_basic_settings_and_generation_time.py`
- `add_coherence_settings.py`
- `add_conversation_history.py` (Master Mode)
- `add_extraction_fields.py`
- `add_generation_groups.py`
- `add_llm_specification_and_scene_plan.py`
- `add_parent_generation_id.py`
- `add_quality_metrics.py`
- `add_seed_value.py`
- `add_temp_clip_paths_and_cancellation.py`
- `add_title_to_generations.py`
- `add_video_url_and_thumbnail_url.py`
- `create_brand_product_image_tables.py`
- `create_editing_sessions_table.py`
- `run_all.py` - Executes all migrations

### Running Migrations

```bash
# Run all migrations
cd backend
python -m app.db.migrations.run_all

# Or use the convenience script
python run_migrations.py
```

---

## Database Initialization

**Script:** `backend/app/db/init_db.py`

```bash
# Create tables
python -m app.db.init_db
```

Creates all tables based on SQLAlchemy models.

---

## Connection Configuration

**File:** `backend/app/db/base.py`

**Environment Variables:**
```bash
# Development (SQLite)
DATABASE_URL=sqlite:///./ad_mint_ai.db

# Production (PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**Engine Settings:**
```python
# SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
```

---

## Session Management

**File:** `backend/app/db/session.py`

```python
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Usage in Routes:**
```python
@router.get("/generations")
def get_generations(db: Session = Depends(get_db)):
    generations = db.query(Generation).all()
    return generations
```

---

## Query Examples

### Get User's Recent Generations

```python
from sqlalchemy import desc

generations = (
    db.query(Generation)
    .filter(Generation.user_id == user_id)
    .filter(Generation.status == "completed")
    .order_by(desc(Generation.created_at))
    .limit(20)
    .all()
)
```

### Get Generation with Quality Metrics

```python
from sqlalchemy.orm import joinedload

generation = (
    db.query(Generation)
    .options(joinedload(Generation.quality_metrics))
    .filter(Generation.id == generation_id)
    .first()
)

# Access metrics
for metric in generation.quality_metrics:
    print(f"{metric.metric_name}: {metric.metric_value}")
```

### Get Comparison Group with All Variations

```python
group = (
    db.query(GenerationGroup)
    .options(joinedload(GenerationGroup.generations))
    .filter(GenerationGroup.id == group_id)
    .first()
)

# Compare generations
for gen in group.generations:
    print(f"Seed {gen.seed_value}: Score {gen.progress}")
```

### Find Edited Versions of a Generation

```python
edited_versions = (
    db.query(Generation)
    .filter(Generation.parent_generation_id == original_id)
    .order_by(Generation.created_at)
    .all()
)
```

---

## Data Retention & Cleanup

### Temporary Files

**Location:** `backend/temp/master_mode/{user_id}/{generation_id}/`

**Contents:**
- Reference images
- Scene videos
- Final stitched video

**Cleanup:** Manual (no automatic cleanup implemented)

### Database Cleanup

**Cascade Deletes:**
- Deleting a `User` → deletes all related `generations`, `brand_styles`, etc.
- Deleting a `Generation` → deletes all related `quality_metrics`
- Deleting a `GenerationGroup` → does NOT delete child generations (nullable FK)

---

## Performance Considerations

### Indexes

All foreign keys are indexed for fast joins.

Additional indexes on:
- `generations.status` - for querying pending/active generations
- `generations.created_at` - for sorting by recency
- `users.username`, `users.email` - for login lookups

### JSON Field Queries

For PostgreSQL, use JSONB operators:

```python
# Find generations with specific framework in llm_specification
generations = (
    db.query(Generation)
    .filter(Generation.llm_specification["framework"].astext == "PAS")
    .all()
)
```

For SQLite, JSON queries are limited. Prefer storing filterable fields as dedicated columns.

---

## Backup & Recovery

### SQLite Backup

```bash
# Backup
cp backend/ad_mint_ai.db backend/ad_mint_ai.db.backup

# Restore
cp backend/ad_mint_ai.db.backup backend/ad_mint_ai.db
```

### PostgreSQL Backup

```bash
# Backup
pg_dump -U user -h host -d ad_mint_ai > backup.sql

# Restore
psql -U user -h host -d ad_mint_ai < backup.sql
```

---

## Schema Evolution Strategy

1. **Create Migration Script:** Add new migration file in `backend/app/db/migrations/`
2. **Update Model:** Modify SQLAlchemy model in `backend/app/db/models/`
3. **Run Migration:** Execute migration script
4. **Update Schemas:** Update Pydantic schemas in `backend/app/schemas/`
5. **Update API:** Modify routes to use new fields

**Best Practices:**
- Always use nullable fields for new columns (backward compatibility)
- Provide default values where possible
- Test migrations on SQLite before PostgreSQL
- Keep migration scripts idempotent (check if already applied)
