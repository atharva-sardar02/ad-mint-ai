#!/usr/bin/env python3
"""
CLI tool to automatically concatenate the best videos from each clip directory.

Usage:
    python concatenate_videos.py <video_generation_dir> [--output OUTPUT] [--no-transitions] [--verbose]

Examples:
    # Basic usage - concatenate best videos from each clip
    python concatenate_videos.py output/video_generations/20251118_113746

    # Custom output path
    python concatenate_videos.py output/video_generations/20251118_113746 --output final_video.mp4

    # Without transitions
    python concatenate_videos.py output/video_generations/20251118_113746 --no-transitions
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pipeline.stitching import stitch_video_clips
from app.core.logging import setup_logging


def find_best_video_in_clip(clip_dir: Path) -> Optional[Path]:
    """
    Find the best video in a clip directory.
    
    Videos are typically named by rank: clip_XXX_video_001.mp4 (rank 1 = best)
    If multiple videos exist, we prefer video_001 (rank 1), then video_002, etc.
    
    Args:
        clip_dir: Directory containing video files for a clip
        
    Returns:
        Path to the best video, or None if no videos found
    """
    if not clip_dir.exists() or not clip_dir.is_dir():
        return None
    
    # Find all video files in the directory
    video_files = sorted(clip_dir.glob("*.mp4"))
    
    if not video_files:
        return None
    
    # Videos are typically named: clip_XXX_video_001.mp4, clip_XXX_video_002.mp4, etc.
    # Rank 1 (video_001) is the best, so we prefer files with _001, then _002, etc.
    # Sort by filename to get video_001 first
    video_files_sorted = sorted(video_files, key=lambda p: p.name)
    
    # Return the first one (should be video_001 = rank 1 = best)
    return video_files_sorted[0]


def find_all_clip_directories(base_dir: Path) -> List[Path]:
    """
    Find all clip directories in the base directory.
    
    Args:
        base_dir: Base directory containing clip_XXX subdirectories
        
    Returns:
        List of clip directory paths, sorted by clip number
    """
    if not base_dir.exists() or not base_dir.is_dir():
        return []
    
    # Find all directories matching clip_XXX pattern
    clip_dirs = []
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("clip_"):
            try:
                # Extract clip number from directory name (e.g., "clip_001" -> 1)
                clip_num = int(item.name.split("_")[1])
                clip_dirs.append((clip_num, item))
            except (ValueError, IndexError):
                # Skip directories that don't match the pattern
                continue
    
    # Sort by clip number and return paths
    clip_dirs.sort(key=lambda x: x[0])
    return [path for _, path in clip_dirs]


def concatenate_best_videos(
    video_generation_dir: Path,
    output_path: Optional[Path] = None,
    transitions: bool = True,
    verbose: bool = False
) -> Path:
    """
    Concatenate the best videos from each clip directory.
    
    Args:
        video_generation_dir: Directory containing clip_XXX subdirectories
        output_path: Optional output path (default: <base_dir>/final_video.mp4)
        transitions: Whether to apply crossfade transitions (default: True)
        verbose: Enable verbose logging
        
    Returns:
        Path to the concatenated video
        
    Raises:
        ValueError: If no videos found or invalid directory structure
        RuntimeError: If concatenation fails
    """
    if verbose:
        setup_logging(log_level="DEBUG")
    
    video_generation_dir = Path(video_generation_dir).resolve()
    
    if not video_generation_dir.exists():
        raise ValueError(f"Directory not found: {video_generation_dir}")
    
    if not video_generation_dir.is_dir():
        raise ValueError(f"Not a directory: {video_generation_dir}")
    
    # Find all clip directories
    print(f"📁 Scanning directory: {video_generation_dir}")
    clip_dirs = find_all_clip_directories(video_generation_dir)
    
    if not clip_dirs:
        raise ValueError(f"No clip directories found in {video_generation_dir}")
    
    print(f"✓ Found {len(clip_dirs)} clip directories")
    
    # Find best video in each clip directory
    best_videos = []
    for clip_dir in clip_dirs:
        best_video = find_best_video_in_clip(clip_dir)
        if best_video:
            best_videos.append(best_video)
            print(f"  ✓ {clip_dir.name}: {best_video.name}")
        else:
            print(f"  ⚠️  {clip_dir.name}: No videos found")
    
    if not best_videos:
        raise ValueError("No videos found in any clip directory")
    
    print(f"\n📹 Found {len(best_videos)} videos to concatenate:")
    for i, video in enumerate(best_videos, 1):
        print(f"  {i}. {video.parent.name}/{video.name}")
    
    # Determine output path
    if output_path is None:
        output_path = video_generation_dir / "final_video.mp4"
    else:
        output_path = Path(output_path).resolve()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Concatenate videos
    print(f"\n🎬 Concatenating videos...")
    print(f"   Output: {output_path}")
    print(f"   Transitions: {'Enabled' if transitions else 'Disabled'}")
    
    try:
        # Convert Path objects to strings for stitching service
        video_paths = [str(video) for video in best_videos]
        
        result_path = stitch_video_clips(
            clip_paths=video_paths,
            output_path=str(output_path),
            transitions=transitions
        )
        
        print(f"\n✅ Successfully created final video!")
        print(f"   Path: {result_path}")
        
        # Get file size
        file_size_mb = Path(result_path).stat().st_size / (1024 * 1024)
        print(f"   Size: {file_size_mb:.2f} MB")
        
        return Path(result_path)
        
    except Exception as e:
        print(f"\n❌ Error concatenating videos: {e}")
        raise RuntimeError(f"Failed to concatenate videos: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Concatenate the best videos from each clip directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "video_generation_dir",
        type=str,
        help="Directory containing clip_XXX subdirectories with video files"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output path for final video (default: <video_generation_dir>/final_video.mp4)"
    )
    
    parser.add_argument(
        "--no-transitions",
        action="store_true",
        help="Disable crossfade transitions between clips"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    try:
        result_path = concatenate_best_videos(
            video_generation_dir=Path(args.video_generation_dir),
            output_path=Path(args.output) if args.output else None,
            transitions=not args.no_transitions,
            verbose=args.verbose
        )
        
        print(f"\n🎉 Done! Final video saved to: {result_path}")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

