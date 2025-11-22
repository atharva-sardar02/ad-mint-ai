#!/usr/bin/env python3
"""
Standalone CLI tool for storyboard creation.

Usage:
    python create_storyboard.py <prompt_file> [--num-clips N] [--reference-image PATH] [--output-dir DIR] [--verbose]

Examples:
    # Basic usage - creates 3 clips with start/end frames
    python create_storyboard.py clip_prompt.txt

    # Create 5 clips
    python create_storyboard.py clip_prompt.txt --num-clips 5

    # With reference image for storyboard prompt enhancement (visual coherence and narrative generation)
    python create_storyboard.py clip_prompt.txt --reference-image output/image_generations/20251117_164104/image_001.png

    # Custom output directory
    python create_storyboard.py clip_prompt.txt --output-dir ./my_storyboard

    # Read from stdin
    echo "A product showcase video" | python create_storyboard.py -
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pipeline.storyboard_service import create_storyboard
from app.core.config import settings
from app.core.logging import setup_logging


def load_prompt(input_source: str) -> str:
    """Load prompt from file or stdin."""
    if input_source == "-":
        print("Enter your video clip prompt (Ctrl+D or Ctrl+Z to finish):")
        prompt = sys.stdin.read().strip()
        if not prompt:
            raise ValueError("No prompt provided from stdin")
        return prompt
    else:
        input_path = Path(input_source)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_source}")
        return input_path.read_text(encoding="utf-8").strip()


def print_storyboard_summary(result):
    """Print storyboard summary to console."""
    print("\n" + "=" * 70)
    print("STORYBOARD CREATION RESULTS")
    print("=" * 70)
    
    print(f"\n📊 Storyboard Summary:")
    print(f"   Total Clips: {len(result.clips)}")
    print(f"   Output Directory: {result.output_dir}")
    print(f"   Framework: {result.metadata.get('framework', 'N/A')}")
    print(f"   Total Duration: {result.metadata.get('total_duration', 0)}s")
    
    # Show narrative document if available
    if result.metadata.get('unified_narrative_path'):
        print(f"\n📖 Unified Narrative Document:")
        print(f"   Path: {result.metadata.get('unified_narrative_path')}")
        narrative_summary = result.metadata.get('narrative_summary', '')
        if narrative_summary:
            print(f"   Summary: {narrative_summary[:150]}...")
        print(f"   Files: unified_narrative.md, unified_narrative.json (in storyboard_enhancement_trace/)")
    
    print(f"\n🎬 Clips with Start/End Frames:")
    for clip in result.clips:
        print(f"\n   Clip {clip.clip_number}:")
        print(f"   - Description: {clip.clip_description[:80]}...")
        print(f"   - Start Frame: {clip.start_frame_path}")
        print(f"   - End Frame: {clip.end_frame_path}")
        print(f"   - Motion: {clip.motion_description}")
        print(f"   - Camera: {clip.camera_movement} ({clip.shot_size}, {clip.perspective})")
    
    print(f"\n📝 Motion Arcs:")
    for clip in result.clips:
        print(f"   Clip {clip.clip_number}: {clip.motion_description}")
    
    print(f"\n📁 File Paths:")
    print(f"   Metadata: {Path(result.output_dir) / 'storyboard_metadata.json'}")
    if result.metadata.get('unified_narrative_path'):
        trace_dir = Path(result.metadata.get('unified_narrative_path')).parent
        print(f"   Narrative MD: {trace_dir / 'unified_narrative.md'}")
        print(f"   Narrative JSON: {trace_dir / 'unified_narrative.json'}")
    for clip in result.clips:
        print(f"   Clip {clip.clip_number} Start: {clip.start_frame_path}")
        print(f"   Clip {clip.clip_number} End: {clip.end_frame_path}")
    
    print("\n" + "=" * 70)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Create storyboards (start and end frames) for video clips",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "prompt_file",
        help="Input file path containing video clip prompt or '-' for stdin"
    )
    
    parser.add_argument(
        "--num-clips",
        type=int,
        default=3,
        help="Number of scenes/clips to create (default: 3, minimum: 1, maximum: 10)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for storyboard files (default: output/storyboards/<timestamp>)"
    )
    
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        default="16:9",
        choices=["1:1", "4:3", "16:9", "9:16"],
        help="Aspect ratio for frames (default: 16:9)"
    )
    
    parser.add_argument(
        "--reference-image",
        type=str,
        default=None,
        help="Path to best image from 8-2 for storyboard prompt enhancement (enables visual coherence)"
    )
    
    parser.add_argument(
        "--total-duration",
        type=int,
        default=15,
        help="Total duration of the final video in seconds (default: 15, valid range: 15-60)"
    )
    
    parser.add_argument(
        "--story-type",
        type=str,
        default="sensory_experience",
        choices=["transformation", "reveal_discovery", "journey_path", "problem_solution", 
                 "sensory_experience", "symbolic_metaphor", "micro_drama", "montage"],
        help="Story type to use for narrative structure (default: sensory_experience). Options: transformation, reveal_discovery, journey_path, problem_solution, sensory_experience, symbolic_metaphor, micro_drama, montage"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Validate num_clips (scenes)
    if args.num_clips < 1:
        print("❌ ERROR: --num-clips must be at least 1")
        sys.exit(1)
    if args.num_clips > 10:
        print("⚠️  WARNING: --num-clips exceeds maximum of 10, will be capped at 10")
        args.num_clips = 10
    
    # Validate total_duration
    if args.total_duration < 15:
        print("❌ ERROR: --total-duration must be at least 15 seconds")
        sys.exit(1)
    if args.total_duration > 60:
        print("❌ ERROR: --total-duration must be at most 60 seconds")
        sys.exit(1)
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level=log_level)
    
    # Check API keys
    if not settings.REPLICATE_API_TOKEN:
        print("❌ ERROR: REPLICATE_API_TOKEN not configured")
        print("   Set it in your .env file or environment variables")
        sys.exit(1)
    
    if args.reference_image and not settings.OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not configured")
        print("   Storyboard prompt enhancement requires OPENAI_API_KEY")
        print("   Set it in your .env file or environment variables")
        sys.exit(1)
    
    if args.reference_image:
        reference_path = Path(args.reference_image)
        if not reference_path.exists():
            print(f"❌ ERROR: Reference image not found: {args.reference_image}")
            sys.exit(1)
    
    # Record start time
    start_time = time.time()
    
    try:
        # Load prompt
        print(f"📖 Loading prompt from: {args.prompt_file if args.prompt_file != '-' else 'stdin'}")
        prompt = load_prompt(args.prompt_file)
        print(f"✓ Loaded prompt ({len(prompt)} characters)")
        
        # Setup output directory
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output") / "storyboards" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {output_dir}")
        print(f"\n🚀 Starting storyboard creation...")
        print(f"   Number of clips: {args.num_clips}")
        print(f"   Aspect ratio: {args.aspect_ratio}")
        print(f"   Total duration: {args.total_duration} seconds")
        print(f"   Story type: {args.story_type}")
        if args.reference_image:
            print(f"   Reference image: {args.reference_image}")
        
        # Create storyboard
        result = await create_storyboard(
            prompt=prompt,
            num_clips=args.num_clips,
            aspect_ratio=args.aspect_ratio,
            reference_image_path=args.reference_image,
            output_dir=output_dir,
            total_duration=args.total_duration,
            story_type=args.story_type
        )
        
        # Print results
        print_storyboard_summary(result)
        
        # Calculate and display elapsed time
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        if minutes > 0:
            print(f"\n⏱️  Total execution time: {minutes}m {seconds}s ({elapsed_time:.2f} seconds)")
        else:
            print(f"\n⏱️  Total execution time: {seconds}s ({elapsed_time:.2f} seconds)")
        
        print("\n✅ Storyboard creation complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

