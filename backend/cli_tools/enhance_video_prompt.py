#!/usr/bin/env python3
"""
Standalone CLI tool for video prompt enhancement.

Usage:
    python enhance_video_prompt.py <input_file> [--video-mode] [--image-to-video] [--storyboard PATH] [--output-dir <dir>] [--max-iterations <n>] [--threshold <score>]

Examples:
    # Basic usage - reads from prompt.txt, saves to output/video_prompt_traces/
    python enhance_video_prompt.py prompt.txt --video-mode

    # Image-to-video mode
    python enhance_video_prompt.py prompt.txt --video-mode --image-to-video

    # Storyboard mode (processes all clips from storyboard_metadata.json)
    python enhance_video_prompt.py --storyboard output/storyboards/20250117_143022/storyboard_metadata.json

    # Custom output directory
    python enhance_video_prompt.py prompt.txt --output-dir ./my_traces

    # Custom iteration settings
    python enhance_video_prompt.py prompt.txt --max-iterations 5 --threshold 90

    # Read from stdin
    echo "A cat in a city" | python enhance_video_prompt.py - --video-mode
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pipeline.video_prompt_enhancement import (
    enhance_video_prompt_iterative,
    enhance_storyboard_motion_prompts
)
from app.core.config import settings
from app.core.logging import setup_logging


def load_prompt(input_source: str) -> str:
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


def print_results(result, output_dir: Path, is_storyboard: bool = False):
    """Print enhancement results to console."""
    print("\n" + "=" * 70)
    print("VIDEO PROMPT ENHANCEMENT RESULTS")
    print("=" * 70)
    
    if is_storyboard:
        print(f"\n📊 Processed {len(result.clips)} clips")
        print(f"   Average Score: {result.summary['average_score']:.1f}/100")
        print(f"   Min Score: {result.summary['min_score']:.1f}/100")
        print(f"   Max Score: {result.summary['max_score']:.1f}/100")
        print(f"   Total Iterations: {result.summary['total_iterations']}")
        
        print("\n📝 Enhanced Motion Prompts by Clip:")
        for clip in result.clips:
            print(f"\n   Clip {clip['clip_number']}:")
            print(f"   - Score: {clip['scores']['overall']:.1f}/100")
            print(f"   - Completeness:    {clip['scores']['completeness']:.1f}/100")
            print(f"   - Specificity:      {clip['scores']['specificity']:.1f}/100")
            print(f"   - Professionalism:  {clip['scores']['professionalism']:.1f}/100")
            print(f"   - Cinematography:   {clip['scores']['cinematography']:.1f}/100")
            print(f"   - Temporal Coherence: {clip['scores']['temporal_coherence']:.1f}/100")
            print(f"   - Brand Alignment:  {clip['scores']['brand_alignment']:.1f}/100")
            if clip.get('start_frame_path'):
                print(f"   - Start Frame: {clip['start_frame_path']}")
            if clip.get('end_frame_path'):
                print(f"   - End Frame: {clip['end_frame_path']}")
            print(f"   - Enhanced Motion Prompt:")
            print(f"     {clip['enhanced_motion_prompt'][:200]}...")
        
        print(f"\n📁 Trace files saved to: {output_dir}")
        print(f"   - Summary: storyboard_enhanced_motion_prompts.json")
        print(f"   - Per-clip traces: clip_001/, clip_002/, etc.")
        print(f"   - Enhanced prompts: clip_001_enhanced_motion_prompt.txt, etc.")
    else:
        print(f"\n📊 Final Score: {result.final_score['overall']:.1f}/100")
        print(f"   Completeness:    {result.final_score['completeness']:.1f}/100")
        print(f"   Specificity:     {result.final_score['specificity']:.1f}/100")
        print(f"   Professionalism: {result.final_score['professionalism']:.1f}/100")
        print(f"   Cinematography:  {result.final_score['cinematography']:.1f}/100")
        print(f"   Temporal Coherence: {result.final_score['temporal_coherence']:.1f}/100")
        print(f"   Brand Alignment: {result.final_score['brand_alignment']:.1f}/100")
        
        print(f"\n🔄 Total Iterations: {result.total_iterations}")
        
        if result.iterations:
            print("\n📝 Iteration History:")
            for i, iteration in enumerate(result.iterations, 1):
                print(f"\n   Iteration {i}:")
                print(f"   - Score: {iteration['scores']['overall']:.1f}/100")
                print(f"   - Key Improvements: {', '.join(iteration['improvements'][:2])}")
        
        if result.motion_prompt:
            print(f"\n🎬 Motion Prompt (for image-to-video):")
            print(f"   {result.motion_prompt}")
        
        print(f"\n📁 Trace files saved to: {output_dir}")
        print(f"   - Original prompt: 00_original_prompt.txt")
        print(f"   - Final prompt: 05_final_enhanced_prompt.txt")
        if result.videodirectorgpt_plan:
            print(f"   - VideoDirectorGPT plan: 06_videodirectorgpt_plan.json")
        print(f"   - Summary: prompt_trace_summary.json")
    
    print("\n" + "=" * 70)
    if not is_storyboard:
        print("FINAL ENHANCED PROMPT")
        print("=" * 70)
        print(result.final_prompt)
        print("=" * 70)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enhance video prompts using two-agent iterative refinement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "input",
        nargs="?",
        help="Input file path or '-' for stdin (mutually exclusive with --storyboard)"
    )
    input_group.add_argument(
        "--storyboard",
        type=str,
        help="Path to storyboard_metadata.json from Story 8.3/8.4 (mutually exclusive with input file/stdin)"
    )
    
    parser.add_argument(
        "--video-mode",
        action="store_true",
        default=True,
        help="Enable video-specific enhancement (default: True)"
    )
    
    parser.add_argument(
        "--image-to-video",
        action="store_true",
        help="Enable image-to-video motion prompt mode"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for trace files (default: output/video_prompt_traces/<timestamp>)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        choices=range(1, 6),
        help="Maximum iteration rounds (default: 3, range: 1-5)"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=85.0,
        help="Score threshold for early stopping (default: 85.0)"
    )
    
    parser.add_argument(
        "--creative-model",
        type=str,
        default="gpt-4-turbo",
        help="Model for Video Director agent (default: gpt-4-turbo)"
    )
    
    parser.add_argument(
        "--critique-model",
        type=str,
        default="gpt-4-turbo",
        help="Model for Prompt Engineer agent (default: gpt-4-turbo)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level=log_level)
    
    # Check API key
    if not settings.OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not configured")
        print("   Set it in your .env file or environment variables")
        sys.exit(1)
    
    try:
        # Setup output directory
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output") / "video_prompt_traces" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle storyboard mode
        if args.storyboard:
            storyboard_path = Path(args.storyboard)
            if not storyboard_path.exists():
                raise FileNotFoundError(f"Storyboard file not found: {args.storyboard}")
            
            print(f"📖 Loading storyboard from: {args.storyboard}")
            print(f"📁 Output directory: {output_dir}")
            print(f"\n🚀 Starting storyboard motion prompt enhancement...")
            print(f"   Max iterations per clip: {args.max_iterations}")
            print(f"   Score threshold: {args.threshold}")
            print(f"   Creative model: {args.creative_model}")
            print(f"   Critique model: {args.critique_model}")
            
            # Enhance storyboard motion prompts
            result = await enhance_storyboard_motion_prompts(
                storyboard_path=storyboard_path,
                max_iterations=args.max_iterations,
                score_threshold=args.threshold,
                creative_model=args.creative_model,
                critique_model=args.critique_model,
                trace_dir=output_dir
            )
            
            # Print results
            print_results(result, output_dir, is_storyboard=True)
            
            print("\n✅ Storyboard enhancement complete!")
            print(f"   Enhanced motion prompts ready for Story 9.2 video generation")
            print(f"   Start/end frame paths preserved in summary JSON")
            print(f"   Unified narrative document reference preserved")
        
        # Handle single prompt mode
        else:
            if not args.input:
                parser.error("Either input file/stdin or --storyboard must be provided")
            
            print(f"📖 Loading prompt from: {args.input if args.input != '-' else 'stdin'}")
            original_prompt = load_prompt(args.input)
            print(f"✓ Loaded prompt ({len(original_prompt)} characters)")
            
            print(f"📁 Output directory: {output_dir}")
            print(f"\n🚀 Starting video prompt enhancement...")
            print(f"   Max iterations: {args.max_iterations}")
            print(f"   Score threshold: {args.threshold}")
            print(f"   Video mode: {args.video_mode}")
            print(f"   Image-to-video mode: {args.image_to_video}")
            print(f"   Creative model: {args.creative_model}")
            print(f"   Critique model: {args.critique_model}")
            
            # Run enhancement
            result = await enhance_video_prompt_iterative(
                user_prompt=original_prompt,
                max_iterations=args.max_iterations,
                score_threshold=args.threshold,
                creative_model=args.creative_model,
                critique_model=args.critique_model,
                trace_dir=output_dir,
                video_mode=args.video_mode,
                image_to_video=args.image_to_video
            )
            
            # Print results
            print_results(result, output_dir, is_storyboard=False)
            
            # Save final prompt to a convenient location
            final_prompt_file = output_dir / "FINAL_PROMPT.txt"
            final_prompt_file.write_text(result.final_prompt, encoding="utf-8")
            print(f"\n✓ Final prompt also saved to: {final_prompt_file}")
            
            if result.motion_prompt:
                motion_prompt_file = output_dir / "MOTION_PROMPT.txt"
                motion_prompt_file.write_text(result.motion_prompt, encoding="utf-8")
                print(f"✓ Motion prompt also saved to: {motion_prompt_file}")
            
            print("\n✅ Enhancement complete!")
        
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

