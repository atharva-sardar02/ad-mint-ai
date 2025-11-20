#!/usr/bin/env python3
"""
Complete Image-to-Video Pipeline Orchestrator

This CLI tool orchestrates the entire pipeline from prompt to final video,
with the ability to stop at any intermediate stage for review.

Pipeline Stages:
    1. Reference Image Generation (hero image from initial prompt)
    2. Narrative Generation (unified story document)
    3. Storyboard Creation (start/end frames for each clip)
    4. Motion Prompt Enhancement (refined prompts for video generation)
    5. Video Clip Generation (individual video clips)
    6. Final Video Assembly (concatenated final output)

Usage:
    # Full pipeline (YOLO mode - no stops)
    python cli_tools/pipeline.py prompt.txt --yolo

    # Stop after reference image
    python cli_tools/pipeline.py prompt.txt --stop-at ref-image

    # Stop after storyboard
    python cli_tools/pipeline.py prompt.txt --stop-at storyboard

    # Stop after clips (don't assemble final video)
    python cli_tools/pipeline.py prompt.txt --stop-at clips

    # Interactive mode (pause at each stage for approval)
    python cli_tools/pipeline.py prompt.txt --interactive

    # Resume from existing output directory
    python cli_tools/pipeline.py --resume output/pipeline_runs/20250119_120000

Examples:
    # Quick test - stop after reference image
    python cli_tools/pipeline.py "A product showcase" --stop-at ref-image

    # Full automated pipeline
    python cli_tools/pipeline.py product_brief.txt --yolo --num-clips 3

    # Interactive with custom settings
    python cli_tools/pipeline.py prompt.txt --interactive --num-clips 5 --duration 30
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pipeline.image_prompt_enhancement import enhance_prompt_iterative
from app.services.image_generation import generate_images
from app.services.pipeline.image_quality_scoring import rank_images_by_quality, score_image
from app.services.pipeline.storyboard_service import create_storyboard
from app.services.pipeline.video_prompt_enhancement import enhance_storyboard_motion_prompts
from app.services.pipeline.video_generation_cli import generate_storyboard_videos
from app.core.config import settings
from app.core.logging import setup_logging


class PipelineOrchestrator:
    """Orchestrates the complete image-to-video pipeline."""

    STAGES = [
        "ref-image",      # Reference image generation
        "narrative",      # Narrative generation (part of storyboard)
        "storyboard",     # Storyboard frames generation
        "motion-prompts", # Motion prompt enhancement
        "clips",          # Video clips generation
        "final-video"     # Final video assembly
    ]

    def __init__(self, args):
        self.args = args
        self.start_time = time.time()
        self.state = {}
        self.output_dir = None

    async def run(self):
        """Execute the pipeline based on configuration."""
        try:
            # Setup output directory
            if self.args.resume:
                self.output_dir = Path(self.args.resume)
                if not self.output_dir.exists():
                    raise ValueError(f"Resume directory not found: {self.args.resume}")
                self.load_state()
                print(f"📁 Resuming from: {self.output_dir}")
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.output_dir = Path("output") / "pipeline_runs" / timestamp
                self.output_dir.mkdir(parents=True, exist_ok=True)
                print(f"📁 Output directory: {self.output_dir}")

            # Load initial prompt
            if not self.args.resume:
                prompt = self.load_prompt(self.args.prompt_file)
                self.state["original_prompt"] = prompt
                self.save_state()

            # Execute pipeline stages
            stages_to_run = self.get_stages_to_run()

            for stage in stages_to_run:
                print(f"\n{'='*70}")
                print(f"STAGE: {stage.upper().replace('-', ' ')}")
                print(f"{'='*70}")

                # Execute stage
                await self.execute_stage(stage)

                # Save state after each stage
                self.save_state()

                # Check if we should stop here
                if self.args.stop_at == stage:
                    self.print_summary(stopped_at=stage)
                    return

                # Interactive mode - pause for approval
                if self.args.interactive and stage != stages_to_run[-1]:
                    if not self.ask_continue(stage):
                        self.print_summary(stopped_at=stage)
                        return

            # Pipeline complete
            self.print_summary()

        except KeyboardInterrupt:
            print("\n\n⚠️  Pipeline interrupted by user")
            self.save_state()
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Pipeline failed at stage: {self.state.get('current_stage', 'unknown')}")
            print(f"   Error: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            self.save_state()
            sys.exit(1)

    def get_stages_to_run(self) -> list:
        """Determine which stages to run based on args and state."""
        if self.args.stop_at:
            # Run up to and including the stop_at stage
            stop_index = self.STAGES.index(self.args.stop_at)
            stages = self.STAGES[:stop_index + 1]
        else:
            # Run all stages
            stages = self.STAGES.copy()

        # If resuming, skip completed stages
        if self.args.resume and "completed_stages" in self.state:
            completed = set(self.state["completed_stages"])
            stages = [s for s in stages if s not in completed]

        return stages

    async def execute_stage(self, stage: str):
        """Execute a single pipeline stage."""
        self.state["current_stage"] = stage

        if stage == "ref-image":
            await self.stage_ref_image()
        elif stage == "narrative":
            await self.stage_narrative()
        elif stage == "storyboard":
            await self.stage_storyboard()
        elif stage == "motion-prompts":
            await self.stage_motion_prompts()
        elif stage == "clips":
            await self.stage_clips()
        elif stage == "final-video":
            await self.stage_final_video()

        # Mark stage as completed
        if "completed_stages" not in self.state:
            self.state["completed_stages"] = []
        self.state["completed_stages"].append(stage)

    async def stage_ref_image(self):
        """Stage 1: Generate reference/hero image from initial prompt."""
        print("\n🎨 Step 1: Enhance prompt and generate reference image...")

        prompt = self.state["original_prompt"]

        # Enhance prompt
        print("   Enhancing prompt...")
        trace_dir = self.output_dir / "01_image_prompt_traces"
        trace_dir.mkdir(exist_ok=True)

        enhancement_result = await enhance_prompt_iterative(
            user_prompt=prompt,
            max_iterations=self.args.prompt_iterations,
            score_threshold=85.0,
            trace_dir=trace_dir,
            image_model_name=self.args.image_model,
            generate_negative=True
        )

        enhanced_prompt = enhancement_result.final_prompt
        negative_prompt = enhancement_result.negative_prompt

        self.state["enhanced_prompt"] = enhanced_prompt
        self.state["negative_prompt"] = negative_prompt

        print(f"   ✓ Prompt enhanced (score: {enhancement_result.final_score['overall']:.1f}/100)")

        # Generate reference image variations
        print(f"   Generating {self.args.ref_image_variations} reference image variations...")
        image_dir = self.output_dir / "02_reference_images"
        image_dir.mkdir(exist_ok=True)

        generation_results = await generate_images(
            prompt=enhanced_prompt,
            num_variations=self.args.ref_image_variations,
            aspect_ratio=self.args.aspect_ratio,
            seed=self.args.seed,
            model_name=self.args.image_model,
            output_dir=image_dir,
            negative_prompt=negative_prompt
        )

        # Score and rank images
        print("   Scoring and ranking images...")
        scored_results = []
        for result in generation_results:
            if result.image_path and Path(result.image_path).exists():
                scores = await score_image(str(result.image_path), enhanced_prompt)
                scored_results.append((str(result.image_path), scores))

        ranked_results = rank_images_by_quality(scored_results)

        # Save best reference image path
        if ranked_results:
            best_path, best_scores, best_rank = ranked_results[0]
            self.state["reference_image_path"] = best_path
            self.state["reference_image_score"] = best_scores["overall"]

            print(f"   ✓ Best reference image: {Path(best_path).name}")
            print(f"     Score: {best_scores['overall']:.1f}/100")
            print(f"     Path: {best_path}")

    async def stage_narrative(self):
        """Stage 2: Generate unified narrative (handled in storyboard stage)."""
        print("\n📖 Step 2: Narrative generation...")
        print("   ℹ️  Narrative will be generated as part of storyboard creation")

    async def stage_storyboard(self):
        """Stage 3: Create storyboard with start/end frames."""
        print(f"\n🎬 Step 3: Create storyboard ({self.args.num_clips} clips)...")

        prompt = self.state["original_prompt"]
        reference_image = self.state.get("reference_image_path")

        storyboard_dir = self.output_dir / "03_storyboard"
        storyboard_dir.mkdir(exist_ok=True)

        result = await create_storyboard(
            prompt=prompt,
            num_clips=self.args.num_clips,
            aspect_ratio=self.args.aspect_ratio,
            reference_image_path=reference_image,
            output_dir=storyboard_dir,
            total_duration=self.args.duration,
            story_type=self.args.story_type
        )

        self.state["storyboard_metadata_path"] = str(storyboard_dir / "storyboard_metadata.json")
        self.state["num_clips"] = len(result.clips)

        if result.metadata.get("unified_narrative_path"):
            self.state["narrative_path"] = result.metadata["unified_narrative_path"]
            print(f"   ✓ Unified narrative generated")

        print(f"   ✓ Storyboard created with {len(result.clips)} clips")
        print(f"     Metadata: {self.state['storyboard_metadata_path']}")

    async def stage_motion_prompts(self):
        """Stage 4: Enhance motion prompts for each clip."""
        print(f"\n✨ Step 4: Enhance motion prompts for {self.state['num_clips']} clips...")

        storyboard_path = Path(self.state["storyboard_metadata_path"])
        trace_dir = self.output_dir / "04_motion_prompt_traces"
        trace_dir.mkdir(exist_ok=True)

        result = await enhance_storyboard_motion_prompts(
            storyboard_path=storyboard_path,
            max_iterations=self.args.prompt_iterations,
            score_threshold=85.0,
            trace_dir=trace_dir
        )

        enhanced_path = trace_dir / "storyboard_enhanced_motion_prompts.json"
        self.state["enhanced_motion_prompts_path"] = str(enhanced_path)

        avg_score = result.summary["average_score"]
        print(f"   ✓ Motion prompts enhanced (avg score: {avg_score:.1f}/100)")
        print(f"     Enhanced prompts: {enhanced_path}")

    async def stage_clips(self):
        """Stage 5: Generate video clips."""
        print(f"\n🎥 Step 5: Generate video clips ({self.args.video_attempts} attempts per clip)...")

        enhanced_prompts_path = self.state["enhanced_motion_prompts_path"]
        video_dir = self.output_dir / "05_video_clips"
        video_dir.mkdir(exist_ok=True)

        result = await generate_storyboard_videos(
            storyboard_json_path=enhanced_prompts_path,
            num_attempts=self.args.video_attempts,
            model_name=self.args.video_model,
            duration=self.args.clip_duration,
            output_dir=video_dir,
            seed=self.args.seed
        )

        self.state["video_clips_dir"] = str(video_dir)
        self.state["total_clips"] = result.summary["total_clips"]
        self.state["total_videos"] = result.summary["total_videos"]
        self.state["total_cost"] = result.summary["total_cost"]

        print(f"   ✓ Generated {result.summary['total_videos']} videos for {result.summary['total_clips']} clips")
        print(f"     Total cost: ${result.summary['total_cost']:.4f}")
        print(f"     Videos saved to: {video_dir}")

    async def stage_final_video(self):
        """Stage 6: Assemble final video from clips."""
        print("\n🎞️  Step 6: Assemble final video...")

        # Import here to avoid dependency issues if not needed
        import subprocess

        video_clips_dir = Path(self.state["video_clips_dir"])
        final_dir = self.output_dir / "06_final_video"
        final_dir.mkdir(exist_ok=True)

        # Find all best videos (rank 001) for each clip
        clip_videos = []
        for clip_num in range(1, self.state["num_clips"] + 1):
            clip_dir = video_clips_dir / f"clip_{clip_num:03d}"
            if clip_dir.exists():
                best_video = clip_dir / f"clip_{clip_num:03d}_video_001.mp4"
                if best_video.exists():
                    clip_videos.append(str(best_video))
                else:
                    print(f"   ⚠️  Warning: Best video not found for clip {clip_num}")

        if not clip_videos:
            print("   ❌ No video clips found to assemble")
            return

        # Create concat file for ffmpeg
        concat_file = final_dir / "concat_list.txt"
        with open(concat_file, "w") as f:
            for video in clip_videos:
                f.write(f"file '{Path(video).absolute()}'\n")

        # Assemble using ffmpeg
        final_video = final_dir / "final_video.mp4"

        print(f"   Concatenating {len(clip_videos)} clips...")

        try:
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(final_video),
                "-y"  # Overwrite if exists
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0 and final_video.exists():
                self.state["final_video_path"] = str(final_video)
                duration = sum([self.args.clip_duration] * len(clip_videos))
                self.state["final_video_duration"] = duration

                print(f"   ✓ Final video assembled")
                print(f"     Duration: ~{duration}s ({len(clip_videos)} clips)")
                print(f"     Path: {final_video}")
            else:
                print(f"   ❌ FFmpeg failed: {result.stderr}")

        except FileNotFoundError:
            print("   ⚠️  FFmpeg not found. Skipping video assembly.")
            print("      Install ffmpeg to enable final video assembly:")
            print("      - macOS: brew install ffmpeg")
            print("      - Ubuntu: sudo apt install ffmpeg")
        except subprocess.TimeoutExpired:
            print("   ❌ Video assembly timed out")

    def load_prompt(self, input_source: str) -> str:
        """Load prompt from file or stdin."""
        if input_source == "-":
            print("Enter your prompt (Ctrl+D or Ctrl+Z to finish):")
            prompt = sys.stdin.read().strip()
            if not prompt:
                raise ValueError("No prompt provided from stdin")
            return prompt
        else:
            input_path = Path(input_source)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_source}")
            return input_path.read_text(encoding="utf-8").strip()

    def save_state(self):
        """Save pipeline state to JSON."""
        state_file = self.output_dir / "pipeline_state.json"
        with open(state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def load_state(self):
        """Load pipeline state from JSON."""
        state_file = self.output_dir / "pipeline_state.json"
        if state_file.exists():
            with open(state_file, "r") as f:
                self.state = json.load(f)

    def ask_continue(self, completed_stage: str) -> bool:
        """Ask user if they want to continue to next stage (interactive mode)."""
        print(f"\n{'─'*70}")
        print(f"✓ Stage '{completed_stage}' completed")
        print(f"{'─'*70}")

        response = input("\nContinue to next stage? [Y/n]: ").strip().lower()
        return response in ["", "y", "yes"]

    def print_summary(self, stopped_at: Optional[str] = None):
        """Print pipeline execution summary."""
        elapsed_time = time.time() - self.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        print("\n" + "="*70)
        print("PIPELINE SUMMARY")
        print("="*70)

        if stopped_at:
            print(f"\n⏸️  Pipeline stopped at: {stopped_at.upper().replace('-', ' ')}")
        else:
            print(f"\n✅ Pipeline completed successfully!")

        print(f"\n📁 Output directory: {self.output_dir}")

        if "completed_stages" in self.state:
            print(f"\n📊 Completed stages:")
            for stage in self.state["completed_stages"]:
                print(f"   ✓ {stage.replace('-', ' ').title()}")

        # Key outputs
        print(f"\n🎯 Key outputs:")
        if "reference_image_path" in self.state:
            print(f"   Reference image: {self.state['reference_image_path']}")
            print(f"   Image score: {self.state.get('reference_image_score', 'N/A'):.1f}/100")

        if "storyboard_metadata_path" in self.state:
            print(f"   Storyboard: {self.state['storyboard_metadata_path']}")
            print(f"   Clips: {self.state.get('num_clips', 'N/A')}")

        if "enhanced_motion_prompts_path" in self.state:
            print(f"   Enhanced prompts: {self.state['enhanced_motion_prompts_path']}")

        if "video_clips_dir" in self.state:
            print(f"   Video clips: {self.state['video_clips_dir']}")
            print(f"   Total videos: {self.state.get('total_videos', 'N/A')}")
            if "total_cost" in self.state:
                print(f"   Total cost: ${self.state['total_cost']:.4f}")

        if "final_video_path" in self.state:
            print(f"   Final video: {self.state['final_video_path']}")
            print(f"   Duration: ~{self.state.get('final_video_duration', 'N/A')}s")

        # Execution time
        if minutes > 0:
            print(f"\n⏱️  Total execution time: {minutes}m {seconds}s")
        else:
            print(f"\n⏱️  Total execution time: {seconds}s")

        # Next steps
        if stopped_at:
            print(f"\n💡 To resume from here:")
            print(f"   python cli_tools/pipeline.py --resume {self.output_dir}")
        elif "final-video" not in self.state.get("completed_stages", []):
            print(f"\n💡 To continue pipeline:")
            print(f"   python cli_tools/pipeline.py --resume {self.output_dir}")

        print("\n" + "="*70)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Complete Image-to-Video Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Input/Resume
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "prompt_file",
        nargs="?",
        help="Input prompt file path or '-' for stdin"
    )
    input_group.add_argument(
        "--resume",
        type=str,
        help="Resume from existing pipeline output directory"
    )

    # Pipeline control
    parser.add_argument(
        "--stop-at",
        type=str,
        choices=PipelineOrchestrator.STAGES,
        help="Stop pipeline at specific stage"
    )
    parser.add_argument(
        "--yolo",
        action="store_true",
        help="Full auto mode - run entire pipeline without stops"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode - pause at each stage for approval"
    )

    # Content settings
    parser.add_argument(
        "--num-clips",
        type=int,
        default=3,
        help="Number of video clips/scenes (default: 3)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=15,
        help="Total video duration in seconds (default: 15)"
    )
    parser.add_argument(
        "--clip-duration",
        type=int,
        default=5,
        help="Individual clip duration in seconds (default: 5)"
    )
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        default="16:9",
        choices=["1:1", "4:3", "16:9", "9:16"],
        help="Aspect ratio (default: 16:9)"
    )
    parser.add_argument(
        "--story-type",
        type=str,
        default="sensory_experience",
        choices=["transformation", "reveal_discovery", "journey_path",
                 "problem_solution", "sensory_experience", "symbolic_metaphor",
                 "micro_drama", "montage"],
        help="Story narrative type (default: sensory_experience)"
    )

    # Generation settings
    parser.add_argument(
        "--ref-image-variations",
        type=int,
        default=4,
        help="Number of reference image variations to generate (default: 4)"
    )
    parser.add_argument(
        "--video-attempts",
        type=int,
        default=3,
        help="Number of video attempts per clip (default: 3)"
    )
    parser.add_argument(
        "--prompt-iterations",
        type=int,
        default=2,
        help="Max prompt enhancement iterations (default: 2)"
    )

    # Model settings
    parser.add_argument(
        "--image-model",
        type=str,
        default="black-forest-labs/flux-schnell",
        help="Replicate image model (default: black-forest-labs/flux-schnell)"
    )
    parser.add_argument(
        "--video-model",
        type=str,
        default="kwaivgi/kling-v2.1",
        help="Replicate video model (default: kwaivgi/kling-v2.1)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed for reproducibility (optional)"
    )

    # Other
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level=log_level)

    # Validate mutual exclusivity
    if args.yolo and args.interactive:
        parser.error("--yolo and --interactive are mutually exclusive")

    if args.yolo and args.stop_at:
        parser.error("--yolo and --stop-at are mutually exclusive")

    # Check API keys
    if not settings.REPLICATE_API_TOKEN:
        print("❌ ERROR: REPLICATE_API_TOKEN not configured")
        print("   Set it in your .env file or environment variables")
        sys.exit(1)

    if not settings.OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not configured")
        print("   Set it in your .env file or environment variables")
        sys.exit(1)

    # Run pipeline
    orchestrator = PipelineOrchestrator(args)
    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())
