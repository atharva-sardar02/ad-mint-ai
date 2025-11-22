#!/usr/bin/env python3
"""
Standalone CLI tool for video generation with automatic VBench quality scoring.

Usage:
    # Text-to-video mode
    python generate_videos.py enhanced_prompt.txt --num-attempts 3
    
    # Image-to-video mode
    python generate_videos.py --image-to-video --hero-frame path/to/image.png --motion-prompt "camera pans left"
    
    # Storyboard mode
    python generate_videos.py --storyboard path/to/storyboard_enhanced_motion_prompts.json

Examples:
    # Basic text-to-video - generates 3 videos with default settings
    python generate_videos.py enhanced_prompt.txt
    
    # Custom number of attempts and model
    python generate_videos.py enhanced_prompt.txt --num-attempts 5 --model klingai/kling-2.5-turbo
    
    # Image-to-video with hero frame
    python generate_videos.py --image-to-video --hero-frame hero.png --motion-prompt "slow zoom in"
    
    # Storyboard mode
    python generate_videos.py --storyboard output/video_prompt_traces/20251117_211447/storyboard_enhanced_motion_prompts.json
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pipeline.video_generation_cli import (
    generate_text_to_video,
    generate_image_to_video,
    generate_storyboard_videos,
    VideoGenerationResult,
    StoryboardVideoGenerationResult,
)
from app.services.pipeline.video_quality_scoring import (
    score_video,
    score_videos_batch,
    rank_videos_by_quality,
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


def save_video_metadata(
    video_path: str,
    scores: Dict[str, float],
    generation_params: Dict,
    output_dir: Path,
    rank: int,
) -> Path:
    """Save metadata JSON for a video."""
    metadata = {
        "video_path": str(video_path),
        "rank": rank,
        "vbench_scores": scores,
        "generation_params": generation_params,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Determine metadata filename based on video filename
    video_name = Path(video_path).stem
    metadata_path = output_dir / f"{video_name}_metadata.json"
    
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    return metadata_path


def rename_video_by_rank(video_path: str, rank: int, output_dir: Path) -> str:
    """Rename video file to reflect quality rank (video_001.mp4 = best)."""
    old_path = Path(video_path).resolve()
    output_dir = output_dir.resolve()
    
    if not old_path.exists():
        raise FileNotFoundError(f"Source video file not found: {old_path}")
    
    if not old_path.is_file():
        raise ValueError(f"Source path is not a file: {old_path}")
    
    ext = old_path.suffix or ".mp4"
    new_filename = f"video_{rank:03d}{ext}"
    new_path = output_dir / new_filename
    
    # Only rename if paths are different
    if old_path.resolve() != new_path.resolve():
        if new_path.exists():
            new_path.unlink()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)
        
        if not new_path.exists():
            raise RuntimeError(f"Failed to rename {old_path} to {new_path}")
        
        return str(new_path)
    
    return str(old_path)


def rename_storyboard_video_by_rank(
    video_path: str,
    clip_number: int,
    rank: int,
    output_dir: Path,
) -> str:
    """Rename storyboard video file to reflect clip and quality rank (clip_001_video_001.mp4 = best)."""
    old_path = Path(video_path).resolve()
    output_dir = output_dir.resolve()
    
    if not old_path.exists():
        raise FileNotFoundError(f"Source video file not found: {old_path}")
    
    ext = old_path.suffix or ".mp4"
    new_filename = f"clip_{clip_number:03d}_video_{rank:03d}{ext}"
    new_path = output_dir / new_filename
    
    if old_path.resolve() != new_path.resolve():
        if new_path.exists():
            new_path.unlink()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)
        
        if not new_path.exists():
            raise RuntimeError(f"Failed to rename {old_path} to {new_path}")
        
        return str(new_path)
    
    return str(old_path)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate videos with automatic VBench quality scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "prompt_file",
        nargs="?",
        help="Input prompt file path (for text-to-video mode) or '-' for stdin",
    )
    mode_group.add_argument(
        "--image-to-video",
        action="store_true",
        help="Enable image-to-video mode",
    )
    mode_group.add_argument(
        "--storyboard",
        type=str,
        metavar="PATH",
        help="Path to storyboard_enhanced_motion_prompts.json (for storyboard mode)",
    )
    
    # Image-to-video specific arguments
    parser.add_argument(
        "--hero-frame",
        type=str,
        help="Path to hero frame image (required if --image-to-video)",
    )
    parser.add_argument(
        "--motion-prompt",
        type=str,
        help="Motion prompt text (required if --image-to-video)",
    )
    
    # Common arguments
    parser.add_argument(
        "--num-attempts",
        type=int,
        default=3,
        help="Number of video attempts to generate (default: 3)",
    )
    parser.add_argument(
        "--negative-prompt",
        type=str,
        help="Negative prompt text (optional)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for generated videos (default: output/video_generations/<timestamp>)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="kwaivgi/kling-v2.1",
        help="Replicate model to use (default: kwaivgi/kling-v2.1)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        choices=range(3, 8),
        metavar="N",
        help="Video duration in seconds (3-7, default: 5)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed value for reproducibility (optional)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable human-in-the-loop feedback (pause after generation for review)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Validate mode-specific arguments
    if args.image_to_video:
        if not args.hero_frame:
            parser.error("--hero-frame is required when using --image-to-video")
        if not args.motion_prompt:
            parser.error("--motion-prompt is required when using --image-to-video")
    elif args.storyboard:
        # Storyboard mode - no additional validation needed here
        pass
    else:
        # Text-to-video mode
        if not args.prompt_file:
            parser.error("prompt_file is required for text-to-video mode")
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level=log_level)
    
    # Check API key
    if not settings.REPLICATE_API_TOKEN:
        print("❌ ERROR: REPLICATE_API_TOKEN not configured")
        print("   Set it in your .env file or environment variables")
        sys.exit(1)
    
    # Record start time
    start_time = time.time()
    
    try:
        # Setup output directory
        if args.output_dir:
            output_path = Path(args.output_dir)
            if not output_path.is_absolute():
                output_path = (Path.cwd() / output_path).resolve()
            if ".." in str(output_path):
                print("❌ ERROR: Output directory contains '..' - path traversal not allowed")
                sys.exit(1)
            output_dir = output_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output") / "video_generations" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {output_dir}")
        
        # Generate videos based on mode
        if args.storyboard:
            # Storyboard mode
            print(f"\n🎬 Storyboard Mode")
            print(f"   Storyboard JSON: {args.storyboard}")
            print(f"   Model: {args.model}")
            print(f"   Attempts per clip: {args.num_attempts}")
            print(f"   Duration: {args.duration}s")
            
            storyboard_result = await generate_storyboard_videos(
                storyboard_json_path=args.storyboard,
                num_attempts=args.num_attempts,
                model_name=args.model,
                duration=args.duration,
                negative_prompt=args.negative_prompt,
                output_dir=output_dir,
                seed=args.seed,
            )
            
            # Process each clip
            print(f"\n📊 Computing VBench quality scores for {storyboard_result.summary['total_videos']} videos...")
            
            all_clip_results = []
            for clip_result in storyboard_result.clip_results:
                clip_number = clip_result.generation_trace.get("clip_number", 0)
                
                # Score videos for this clip
                video_paths = [v.file_path for v in clip_result.videos]
                prompt_texts = [
                    clip_result.generation_trace.get("motion_prompt", "")
                    for _ in clip_result.videos
                ]
                
                scores_list = score_videos_batch(video_paths, prompt_texts)
                
                # Update video metadata with scores
                for video, scores in zip(clip_result.videos, scores_list):
                    video.vbench_scores = scores
                
                # Rank videos by quality
                ranked_videos = rank_videos_by_quality(video_paths, scores_list)
                
                # Rename videos by rank
                print(f"\n📝 Renaming videos for clip {clip_number} by quality rank...")
                final_video_paths = []
                for video_path, scores, rank in ranked_videos:
                    try:
                        new_path = rename_storyboard_video_by_rank(
                            video_path, clip_number, rank, output_dir / f"clip_{clip_number:03d}"
                        )
                        final_video_paths.append((new_path, scores, rank))
                    except Exception as e:
                        print(f"⚠️  Warning: Failed to rename video {video_path}: {e}")
                        final_video_paths.append((video_path, scores, rank))
                
                # Save metadata for each video
                print(f"💾 Saving metadata files for clip {clip_number}...")
                for video_path, scores, rank in final_video_paths:
                    # Find corresponding video metadata
                    video_meta = next(
                        (v for v in clip_result.videos if v.file_path == video_path or Path(v.file_path).name == Path(video_path).name),
                        None
                    )
                    if video_meta:
                        save_video_metadata(
                            video_path=video_path,
                            scores=scores,
                            generation_params=video_meta.generation_params,
                            output_dir=output_dir / f"clip_{clip_number:03d}",
                            rank=rank,
                        )
                
                # Update video ranks
                for video, (_, _, rank) in zip(clip_result.videos, final_video_paths):
                    video.rank = rank
                
                all_clip_results.append((clip_number, clip_result, final_video_paths))
            
            # Save storyboard video generation trace
            trace_data = {
                "mode": "storyboard",
                "storyboard_path": storyboard_result.storyboard_path,
                "unified_narrative_path": storyboard_result.unified_narrative_path,
                "model": args.model,
                "duration": args.duration,
                "num_attempts": args.num_attempts,
                "negative_prompt": args.negative_prompt,
                "seed": args.seed,
                "timestamp": datetime.now().isoformat(),
                "clips": [],
                "summary": storyboard_result.summary,
            }
            
            for clip_number, clip_result, final_video_paths in all_clip_results:
                clip_data = {
                    "clip_number": clip_number,
                    "videos": [
                        {
                            "file_path": video_path,
                            "rank": rank,
                            "scores": scores,
                            "metadata_file": str(
                                output_dir / f"clip_{clip_number:03d}" / f"{Path(video_path).stem}_metadata.json"
                            ),
                        }
                        for video_path, scores, rank in final_video_paths
                    ],
                    "start_frame_path": clip_result.generation_trace.get("start_frame_path"),
                    "end_frame_path": clip_result.generation_trace.get("end_frame_path"),
                    "enhanced_motion_prompt": clip_result.generation_trace.get("motion_prompt"),
                    "total_cost": clip_result.generation_trace.get("total_cost", 0.0),
                }
                trace_data["clips"].append(clip_data)
            
            trace_path = output_dir / "storyboard_video_generation_trace.json"
            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(trace_data, f, indent=2)
            
            # Print results
            print_storyboard_results(all_clip_results, output_dir, trace_data)
            
        elif args.image_to_video:
            # Image-to-video mode
            print(f"\n🎬 Image-to-Video Mode")
            print(f"   Hero frame: {args.hero_frame}")
            print(f"   Motion prompt: {args.motion_prompt[:100]}...")
            print(f"   Model: {args.model}")
            print(f"   Attempts: {args.num_attempts}")
            print(f"   Duration: {args.duration}s")
            
            result = await generate_image_to_video(
                hero_frame_path=args.hero_frame,
                motion_prompt=args.motion_prompt,
                num_attempts=args.num_attempts,
                model_name=args.model,
                duration=args.duration,
                negative_prompt=args.negative_prompt,
                output_dir=output_dir,
                seed=args.seed,
            )
            
            # Score videos
            print(f"\n📊 Computing VBench quality scores for {len(result.videos)} videos...")
            video_paths = [v.file_path for v in result.videos]
            prompt_texts = [result.generation_trace.get("motion_prompt", "") for _ in result.videos]
            scores_list = score_videos_batch(video_paths, prompt_texts)
            
            # Update video metadata with scores
            for video, scores in zip(result.videos, scores_list):
                video.vbench_scores = scores
            
            # Rank videos by quality
            ranked_videos = rank_videos_by_quality(video_paths, scores_list)
            
            # Rename videos by rank
            print(f"\n📝 Renaming videos by quality rank...")
            final_video_paths = []
            for video_path, scores, rank in ranked_videos:
                try:
                    new_path = rename_video_by_rank(video_path, rank, output_dir)
                    final_video_paths.append((new_path, scores, rank))
                except Exception as e:
                    print(f"⚠️  Warning: Failed to rename video {video_path}: {e}")
                    final_video_paths.append((video_path, scores, rank))
            
            # Save metadata for each video
            print(f"💾 Saving metadata files...")
            for video_path, scores, rank in final_video_paths:
                video_meta = next(
                    (v for v in result.videos if v.file_path == video_path or Path(v.file_path).name == Path(video_path).name),
                    None
                )
                if video_meta:
                    save_video_metadata(
                        video_path=video_path,
                        scores=scores,
                        generation_params=video_meta.generation_params,
                        output_dir=output_dir,
                        rank=rank,
                    )
            
            # Update video ranks
            for video, (_, _, rank) in zip(result.videos, final_video_paths):
                video.rank = rank
            
            # Save generation trace
            trace_data = {
                "mode": "image-to-video",
                "hero_frame_path": result.hero_frame_path,
                "motion_prompt": result.generation_trace.get("motion_prompt"),
                "negative_prompt": args.negative_prompt,
                "model": args.model,
                "duration": args.duration,
                "num_attempts": args.num_attempts,
                "seed": args.seed,
                "timestamp": datetime.now().isoformat(),
                "videos": [
                    {
                        "file_path": video_path,
                        "rank": rank,
                        "scores": scores,
                        "metadata_file": str(output_dir / f"{Path(video_path).stem}_metadata.json"),
                    }
                    for video_path, scores, rank in final_video_paths
                ],
                "costs": {
                    "total": result.generation_trace.get("total_cost", 0.0),
                    "per_video": result.generation_trace.get("total_cost", 0.0) / len(final_video_paths) if final_video_paths else 0.0,
                },
            }
            
            trace_path = output_dir / "generation_trace.json"
            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(trace_data, f, indent=2)
            
            # Print results
            print_video_results(final_video_paths, output_dir, trace_data, result)
            
        else:
            # Text-to-video mode
            print(f"📖 Loading prompt from: {args.prompt_file if args.prompt_file != '-' else 'stdin'}")
            prompt = load_prompt(args.prompt_file)
            print(f"✓ Loaded prompt ({len(prompt)} characters)")
            
            print(f"\n🎬 Text-to-Video Mode")
            print(f"   Model: {args.model}")
            print(f"   Attempts: {args.num_attempts}")
            print(f"   Duration: {args.duration}s")
            print(f"   Seed: {args.seed if args.seed else 'random'}")
            
            result = await generate_text_to_video(
                prompt=prompt,
                num_attempts=args.num_attempts,
                model_name=args.model,
                duration=args.duration,
                negative_prompt=args.negative_prompt,
                output_dir=output_dir,
                seed=args.seed,
            )
            
            # Score videos
            print(f"\n📊 Computing VBench quality scores for {len(result.videos)} videos...")
            video_paths = [v.file_path for v in result.videos]
            prompt_texts = [prompt for _ in result.videos]
            scores_list = score_videos_batch(video_paths, prompt_texts)
            
            # Update video metadata with scores
            for video, scores in zip(result.videos, scores_list):
                video.vbench_scores = scores
            
            # Rank videos by quality
            ranked_videos = rank_videos_by_quality(video_paths, scores_list)
            
            # Rename videos by rank
            print(f"\n📝 Renaming videos by quality rank...")
            final_video_paths = []
            for video_path, scores, rank in ranked_videos:
                try:
                    new_path = rename_video_by_rank(video_path, rank, output_dir)
                    final_video_paths.append((new_path, scores, rank))
                except Exception as e:
                    print(f"⚠️  Warning: Failed to rename video {video_path}: {e}")
                    final_video_paths.append((video_path, scores, rank))
            
            # Save metadata for each video
            print(f"💾 Saving metadata files...")
            for video_path, scores, rank in final_video_paths:
                video_meta = next(
                    (v for v in result.videos if v.file_path == video_path or Path(v.file_path).name == Path(video_path).name),
                    None
                )
                if video_meta:
                    save_video_metadata(
                        video_path=video_path,
                        scores=scores,
                        generation_params=video_meta.generation_params,
                        output_dir=output_dir,
                        rank=rank,
                    )
            
            # Update video ranks
            for video, (_, _, rank) in zip(result.videos, final_video_paths):
                video.rank = rank
            
            # Save generation trace
            trace_data = {
                "mode": "text-to-video",
                "prompt": prompt,
                "negative_prompt": args.negative_prompt,
                "model": args.model,
                "duration": args.duration,
                "num_attempts": args.num_attempts,
                "seed": args.seed,
                "timestamp": datetime.now().isoformat(),
                "videos": [
                    {
                        "file_path": video_path,
                        "rank": rank,
                        "scores": scores,
                        "metadata_file": str(output_dir / f"{Path(video_path).stem}_metadata.json"),
                    }
                    for video_path, scores, rank in final_video_paths
                ],
                "costs": {
                    "total": result.generation_trace.get("total_cost", 0.0),
                    "per_video": result.generation_trace.get("total_cost", 0.0) / len(final_video_paths) if final_video_paths else 0.0,
                },
            }
            
            trace_path = output_dir / "generation_trace.json"
            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(trace_data, f, indent=2)
            
            # Print results
            print_video_results(final_video_paths, output_dir, trace_data, result)
        
        # Calculate and display elapsed time
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        if minutes > 0:
            print(f"\n⏱️  Total execution time: {minutes}m {seconds}s ({elapsed_time:.2f} seconds)")
        else:
            print(f"\n⏱️  Total execution time: {seconds}s ({elapsed_time:.2f} seconds)")
        
        print("\n✅ Video generation complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_video_results(
    ranked_videos: List[Tuple[str, Dict, int]],
    output_dir: Path,
    trace_data: Dict,
    result: VideoGenerationResult,
):
    """Print video generation results to console."""
    print("\n" + "=" * 70)
    print("VIDEO GENERATION RESULTS")
    print("=" * 70)
    
    print(f"\n📊 Generated {len(ranked_videos)} videos")
    print(f"💰 Total cost: ${trace_data.get('costs', {}).get('total', 0):.4f}")
    per_video = trace_data.get('costs', {}).get('per_video', 0)
    if per_video:
        print(f"   Per-video cost: ${per_video:.4f}")
    print(f"📁 Output directory: {output_dir}")
    
    print("\n🏆 RANKED VIDEOS (by overall quality score):")
    print("-" * 70)
    
    # Print top 3
    for i, (video_path, scores, rank) in enumerate(ranked_videos[:3]):
        marker = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
        print(f"\n{marker} Rank #{rank} (Top {i+1})")
        print(f"   File: {Path(video_path).name}")
        print(f"   Overall Score: {scores.get('overall_quality', 0):.1f}/100")
        print(f"   - Temporal Quality: {scores.get('temporal_quality', 0):.1f}/100")
        print(f"   - Subject Consistency: {scores.get('subject_consistency', 0):.1f}/100")
        print(f"   - Motion Smoothness: {scores.get('motion_smoothness', 0):.1f}/100")
        print(f"   - Aesthetic Quality: {scores.get('aesthetic_quality', 0):.1f}/100")
        print(f"   - Text-Video Alignment: {scores.get('text_video_alignment', 0):.1f}/100")
        print(f"   Path: {video_path}")
    
    # Print remaining videos
    if len(ranked_videos) > 3:
        print(f"\n📋 Remaining videos:")
        for video_path, scores, rank in ranked_videos[3:]:
            print(f"   #{rank}: {Path(video_path).name} (Score: {scores.get('overall_quality', 0):.1f}/100)")
    
    # Best candidate summary
    if ranked_videos:
        best_path, best_scores, best_rank = ranked_videos[0]
        print("\n" + "=" * 70)
        print("SYSTEM-SELECTED BEST VIDEO")
        print("=" * 70)
        print(f"Video: {Path(best_path).name}")
        print(f"Overall Score: {best_scores.get('overall_quality', 0):.1f}/100")
        print(f"\nScore Breakdown:")
        print(f"  • Temporal Quality (40%): {best_scores.get('temporal_quality', 0):.1f}/100")
        print(f"  • Frame-wise Quality (35%): {best_scores.get('aesthetic_quality', 0):.1f}/100")
        print(f"  • Text-Video Alignment (25%): {best_scores.get('text_video_alignment', 0):.1f}/100")
        print(f"\nFull path: {best_path}")
    
    print("\n" + "=" * 70)
    print(f"📄 Trace file: {output_dir / 'generation_trace.json'}")
    print("=" * 70)


def print_storyboard_results(
    all_clip_results: List[Tuple[int, VideoGenerationResult, List]],
    output_dir: Path,
    trace_data: Dict,
):
    """Print storyboard video generation results to console."""
    print("\n" + "=" * 70)
    print("STORYBOARD VIDEO GENERATION RESULTS")
    print("=" * 70)
    
    print(f"\n📊 Generated videos for {len(all_clip_results)} clips")
    print(f"💰 Total cost: ${trace_data.get('summary', {}).get('total_cost', 0):.4f}")
    print(f"📁 Output directory: {output_dir}")
    
    print("\n🎬 CLIPS PROCESSED:")
    print("-" * 70)
    
    for clip_number, clip_result, final_video_paths in all_clip_results:
        print(f"\n📹 Clip {clip_number}")
        if final_video_paths:
            best_path, best_scores, best_rank = final_video_paths[0]
            print(f"   Best video: {Path(best_path).name} (Rank #{best_rank})")
            print(f"   Overall Score: {best_scores.get('overall_quality', 0):.1f}/100")
            print(f"   Total videos: {len(final_video_paths)}")
        else:
            print(f"   ⚠️  No videos generated for this clip")
    
    print("\n" + "=" * 70)
    print(f"📄 Trace file: {output_dir / 'storyboard_video_generation_trace.json'}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

