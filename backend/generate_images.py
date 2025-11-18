#!/usr/bin/env python3
"""
Standalone CLI tool for image generation with automatic quality scoring.

Usage:
    python generate_images.py <prompt_file> [--num-variations N] [--aspect-ratio R] [--seed N] [--output-dir DIR] [--model M] [--verbose]

Examples:
    # Basic usage - generates 8 images with default settings
    python generate_images.py enhanced_prompt.txt

    # Custom number of variations and aspect ratio
    python generate_images.py enhanced_prompt.txt --num-variations 6 --aspect-ratio 1:1

    # Custom output directory and seed for reproducibility
    python generate_images.py enhanced_prompt.txt --output-dir ./my_images --seed 12345

    # Read from stdin
    echo "A beautiful sunset over mountains" | python generate_images.py -
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.image_generation import generate_images, ImageGenerationResult
from app.services.pipeline.image_quality_scoring import score_image, rank_images_by_quality
from app.services.pipeline.image_prompt_enhancement import (
    enhance_prompt_iterative,
    enhance_prompt_with_image_feedback,
    enhance_prompt_with_parallel_exploration
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


def save_metadata(
    image_path: str,
    scores: Dict[str, float],
    prompt: str,
    model_name: str,
    seed: int,
    output_dir: Path,
    rank: int
) -> Path:
    """Save metadata JSON for an image."""
    metadata = {
        "image_path": str(image_path),
        "rank": rank,
        "scores": scores,
        "prompt": prompt,
        "model": model_name,
        "seed": seed,
        "timestamp": datetime.now().isoformat()
    }
    
    # Determine metadata filename based on image filename
    image_name = Path(image_path).stem
    metadata_path = output_dir / f"{image_name}_metadata.json"
    
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    return metadata_path


def rename_image_by_rank(image_path: str, rank: int, output_dir: Path) -> str:
    """Rename image file to reflect quality rank (image_001.png = best)."""
    old_path = Path(image_path).resolve()  # Use absolute path
    output_dir = output_dir.resolve()  # Use absolute path
    
    # Verify source file exists and is readable
    if not old_path.exists():
        raise FileNotFoundError(f"Source image file not found: {old_path}")
    
    if not old_path.is_file():
        raise ValueError(f"Source path is not a file: {old_path}")
    
    ext = old_path.suffix or ".png"
    new_filename = f"image_{rank:03d}{ext}"
    new_path = output_dir / new_filename
    
    # Only rename if paths are different
    if old_path.resolve() != new_path.resolve():
        # If target already exists (from previous run), remove it first
        if new_path.exists():
            new_path.unlink()
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Rename the file
        old_path.rename(new_path)
        
        # Verify the file was moved successfully
        if not new_path.exists():
            raise RuntimeError(f"Failed to rename {old_path} to {new_path}")
        
        return str(new_path)
    
    return str(old_path)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate images with automatic quality scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "prompt_file",
        help="Input prompt file path or '-' for stdin"
    )
    
    parser.add_argument(
        "--num-variations",
        type=int,
        default=8,
        choices=range(1, 9),
        metavar="N",
        help="Number of image variations to generate (1-8, default: 8)"
    )
    
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        default="16:9",
        choices=["1:1", "4:3", "16:9", "9:16"],
        help="Aspect ratio for generated images (default: 16:9)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed value for reproducibility (optional)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for generated images (default: output/image_generations/<timestamp>)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="black-forest-labs/flux-schnell",
        help="Replicate model to use (default: black-forest-labs/flux-schnell). Options: black-forest-labs/flux-schnell, google/nano-banana, black-forest-labs/flux-dev, stability-ai/sdxl-turbo"
    )
    
    parser.add_argument(
        "--enhance-mode",
        type=str,
        choices=["prompt-only", "image-feedback", "parallel-exploration", "none"],
        default="prompt-only",
        help="Enhancement mode: 'prompt-only' (fast, uses prompt scoring), 'image-feedback' (sequential image feedback), 'parallel-exploration' (test multiple variations simultaneously), 'none' (skip enhancement)"
    )
    
    parser.add_argument(
        "--no-negative-prompt",
        action="store_true",
        help="Skip negative prompt generation (default: generate negative prompts)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of enhancement iterations (default: 2 for image-feedback/parallel-exploration, 3 for prompt-only). Higher = more refinement but more cost."
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
    if not settings.REPLICATE_API_TOKEN:
        print("❌ ERROR: REPLICATE_API_TOKEN not configured")
        print("   Set it in your .env file or environment variables")
        sys.exit(1)
    
    # Record start time
    start_time = time.time()
    
    try:
        # Load prompt
        print(f"📖 Loading prompt from: {args.prompt_file if args.prompt_file != '-' else 'stdin'}")
        original_prompt = load_prompt(args.prompt_file)
        print(f"✓ Loaded prompt ({len(original_prompt)} characters)")
        
        # Enhance prompt if requested
        prompt = original_prompt
        negative_prompt = None
        enhancement_result = None
        
        if args.enhance_mode != "none":
            print(f"\n🔧 Enhancing prompt (mode: {args.enhance_mode})...")
            print(f"   Model: {args.model}")
            
            # Create trace directory for enhancement
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            trace_dir = Path("output") / "image_prompt_traces" / timestamp
            trace_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine max_iterations based on mode and user input
            if args.max_iterations is not None:
                max_iterations = args.max_iterations
            else:
                # Default iterations per mode
                if args.enhance_mode == "prompt-only":
                    max_iterations = 3
                else:  # image-feedback or parallel-exploration
                    max_iterations = 2
            
            if args.enhance_mode == "image-feedback":
                print(f"   Using sequential image feedback loop (this will generate test images)...")
                print(f"   Max iterations: {max_iterations}")
                enhancement_result = await enhance_prompt_with_image_feedback(
                    user_prompt=original_prompt,
                    image_model_name=args.model,
                    num_test_images=2,
                    max_iterations=max_iterations,
                    score_threshold=70.0,
                    trace_dir=trace_dir,
                    generate_negative=not args.no_negative_prompt,
                    aspect_ratio=args.aspect_ratio,
                    seed=args.seed
                )
            elif args.enhance_mode == "parallel-exploration":
                print(f"   Using parallel exploration (will test {args.num_variations} prompt variations per iteration)...")
                print(f"   Max iterations: {max_iterations}")
                enhancement_result = await enhance_prompt_with_parallel_exploration(
                    user_prompt=original_prompt,
                    image_model_name=args.model,
                    num_variations=args.num_variations,  # Use CLI num_variations for parallel exploration
                    max_iterations=max_iterations,
                    score_threshold=70.0,
                    trace_dir=trace_dir,
                    generate_negative=not args.no_negative_prompt,
                    aspect_ratio=args.aspect_ratio,
                    seed=args.seed
                )
            else:  # prompt-only
                print(f"   Using prompt-only enhancement...")
                print(f"   Max iterations: {max_iterations}")
                enhancement_result = await enhance_prompt_iterative(
                    user_prompt=original_prompt,
                    max_iterations=max_iterations,
                    score_threshold=85.0,
                    trace_dir=trace_dir,
                    image_model_name=args.model,
                    generate_negative=not args.no_negative_prompt
                )
            
            prompt = enhancement_result.final_prompt
            negative_prompt = enhancement_result.negative_prompt
            
            print(f"✓ Enhanced prompt ({len(prompt)} characters)")
            if negative_prompt:
                print(f"✓ Generated negative prompt ({len(negative_prompt)} characters)")
            print(f"📁 Enhancement trace: {trace_dir}")
        
        # Setup output directory with path traversal protection
        if args.output_dir:
            output_path = Path(args.output_dir)
            # Resolve to absolute path
            if not output_path.is_absolute():
                output_path = (Path.cwd() / output_path).resolve()
            # Check for path traversal attempts
            if ".." in str(output_path):
                print("❌ ERROR: Output directory contains '..' - path traversal not allowed")
                sys.exit(1)
            output_dir = output_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output") / "image_generations" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {output_dir}")
        print(f"\n🚀 Starting image generation...")
        print(f"   Model: {args.model}")
        print(f"   Variations: {args.num_variations}")
        print(f"   Aspect ratio: {args.aspect_ratio}")
        print(f"   Seed: {args.seed if args.seed else 'random'}")
        
        # Generate images
        generation_results = await generate_images(
            prompt=prompt,
            num_variations=args.num_variations,
            aspect_ratio=args.aspect_ratio,
            seed=args.seed,
            model_name=args.model,
            output_dir=output_dir,
            negative_prompt=negative_prompt
        )
        
        if not generation_results:
            print("❌ ERROR: No images were generated")
            sys.exit(1)
        
        print(f"\n✓ Generated {len(generation_results)} images")
        
        # Verify all image files exist before scoring
        valid_results = []
        for result in generation_results:
            if result.image_path:
                image_path = Path(result.image_path).resolve()
                if image_path.exists() and image_path.is_file():
                    # Verify file is not empty
                    if image_path.stat().st_size > 0:
                        valid_results.append(result)
                    else:
                        print(f"⚠️  Warning: Image file is empty: {image_path}")
                else:
                    print(f"⚠️  Warning: Image file not found or not a file: {image_path}")
            else:
                print(f"⚠️  Warning: Image path is None for result: {result}")
        
        if not valid_results:
            print("❌ ERROR: No valid image files found for scoring")
            sys.exit(1)
        
        print(f"\n📊 Computing quality scores for {len(valid_results)} images...")
        
        # Score all valid images (shuffle order to avoid any potential bias)
        import random
        scoring_order = list(valid_results)
        random.shuffle(scoring_order)  # Randomize scoring order to avoid any systematic bias
        
        scored_results = []
        for result in scoring_order:
            try:
                image_path = Path(result.image_path).resolve()
                scores = await score_image(str(image_path), prompt)
                scored_results.append((str(image_path), scores))
                if args.verbose:
                    print(f"  Scored {Path(image_path).name}: {scores['overall']:.1f}/100")
            except Exception as e:
                print(f"⚠️  Warning: Failed to score image {image_path}: {e}")
                # Continue with other images
                continue
        
        if not scored_results:
            print("❌ ERROR: No images were scored")
            sys.exit(1)
        
        # Create mapping from original image path to generation result for cost tracking
        path_to_result = {}
        for result in valid_results:
            if result.image_path:
                path_key = str(Path(result.image_path).resolve())
                path_to_result[path_key] = result
        
        # Rank images by quality
        ranked_results = rank_images_by_quality(scored_results)
        
        # Debug: Print all scores before ranking (in verbose mode)
        if args.verbose:
            print(f"\n📊 All image scores (before ranking):")
            for image_path, scores in scored_results:
                print(f"  {Path(image_path).name}: {scores['overall']:.2f}/100 "
                      f"(Pick: {scores.get('pickscore', 0):.1f}, "
                      f"CLIP: {scores.get('clip_score', 0):.1f}, "
                      f"Aesthetic: {scores.get('aesthetic', 0):.1f})")
            print(f"\n📊 After ranking:")
            for image_path, scores, rank in ranked_results:
                print(f"  Rank {rank}: {Path(image_path).name} - {scores['overall']:.2f}/100")
        
        # Rename images by rank using two-phase approach to avoid conflicts
        print(f"\n📝 Renaming images by quality rank...")
        
        # Phase 1: Rename all files to temporary names to avoid conflicts
        temp_paths = []
        for i, (image_path, scores, rank) in enumerate(ranked_results):
            old_path = Path(image_path).resolve()
            output_dir_resolved = output_dir.resolve()
            
            if not old_path.exists():
                print(f"⚠️  Warning: Source image not found: {old_path}")
                temp_paths.append((image_path, scores, rank, image_path))
                continue
            
            # Create temporary filename
            ext = old_path.suffix or ".png"
            temp_filename = f"temp_{i:03d}_{rank:03d}{ext}"
            temp_path = output_dir_resolved / temp_filename
            
            try:
                # Remove temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()
                
                # Rename to temp
                old_path.rename(temp_path)
                
                # Verify rename succeeded
                if not temp_path.exists():
                    raise RuntimeError(f"Failed to rename {old_path} to {temp_path}")
                
                temp_paths.append((str(temp_path), scores, rank, image_path))
            except Exception as e:
                print(f"⚠️  Warning: Failed to rename {old_path} to temp: {e}")
                temp_paths.append((image_path, scores, rank, image_path))
        
        # Phase 2: Rename from temp names to final ranked names
        final_image_paths = []
        for temp_path, scores, rank, original_path in temp_paths:
            temp_path_obj = Path(temp_path).resolve()
            output_dir_resolved = output_dir.resolve()
            
            if not temp_path_obj.exists():
                print(f"⚠️  Warning: Temp file not found: {temp_path_obj}")
                final_image_paths.append((temp_path, scores, rank, original_path))
                continue
            
            # Create final ranked filename
            ext = temp_path_obj.suffix or ".png"
            final_filename = f"image_{rank:03d}{ext}"
            final_path = output_dir_resolved / final_filename
            
            try:
                # Remove final file if it exists (shouldn't happen, but be safe)
                if final_path.exists():
                    final_path.unlink()
                
                # Rename from temp to final
                temp_path_obj.rename(final_path)
                
                # Verify rename succeeded
                if not final_path.exists():
                    raise RuntimeError(f"Failed to rename {temp_path_obj} to {final_path}")
                
                final_image_paths.append((str(final_path), scores, rank, original_path))
            except Exception as e:
                print(f"⚠️  Warning: Failed to rename {temp_path_obj} to final: {e}")
                # Try to keep temp file if final rename failed
                final_image_paths.append((temp_path, scores, rank, original_path))
        
        # Save metadata for each image
        print(f"\n💾 Saving metadata files...")
        metadata_paths = []
        for image_path, scores, rank, original_path in final_image_paths:
            metadata_path = save_metadata(
                image_path=image_path,
                scores=scores,
                prompt=prompt,
                model_name=args.model,
                seed=args.seed or 0,
                output_dir=output_dir,
                rank=rank
            )
            metadata_paths.append(metadata_path)
        
        # Save generation trace
        # Use enhancement result if available
        if enhancement_result:
            original_prompt = enhancement_result.original_prompt
            enhanced_prompt = enhancement_result.final_prompt
        else:
            original_prompt = prompt
            enhanced_prompt = prompt
        
        # Build images array with proper cost mapping
        images_data = []
        for (image_path, scores, rank, original_path), metadata_path in zip(final_image_paths, metadata_paths):
            # Find corresponding generation result using original path
            original_path_key = str(Path(original_path).resolve())
            result = path_to_result.get(original_path_key)
            
            image_data = {
                "path": str(image_path),
                "rank": rank,
                "scores": scores,
                "metadata_file": str(metadata_path),
                "is_best_candidate": rank == 1,
                "cost": result.cost if result else 0.0,
                "generation_time": result.generation_time if result else 0.0
            }
            images_data.append(image_data)
        
        trace_data = {
            "prompt": {
                "original": original_prompt,
                "enhanced": enhanced_prompt,
                "used": enhanced_prompt  # The prompt actually used for generation
            },
            "model": args.model,
            "seed": args.seed,
            "aspect_ratio": args.aspect_ratio,
            "num_variations": args.num_variations,
            "timestamp": datetime.now().isoformat(),
            "images": images_data,
            "costs": {
                "total": sum(r.cost for r in generation_results),
                "per_image": generation_results[0].cost if generation_results else 0.0,
                "breakdown": [
                    {
                        "image_rank": i + 1,
                        "cost": r.cost,
                        "model": r.model_name
                    }
                    for i, r in enumerate(generation_results)
                ]
            },
            "api_calls": [
                {
                    "timestamp": r.timestamp,
                    "model": r.model_name,
                    "cost": r.cost,
                    "generation_time": r.generation_time,
                    "seed": r.seed
                }
                for r in generation_results
            ]
        }
        
        trace_path = output_dir / "generation_trace.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(trace_data, f, indent=2)
        
        # Create best candidate symlink and mark in metadata
        if final_image_paths:
            best_path, best_scores, best_rank, _ = final_image_paths[0]
            best_path_abs = Path(best_path).resolve()  # Use absolute path
            
            # Verify best image file exists and is readable
            if not best_path_abs.exists():
                print(f"⚠️  Warning: Best candidate image not found: {best_path_abs}")
            elif not best_path_abs.is_file():
                print(f"⚠️  Warning: Best candidate path is not a file: {best_path_abs}")
            else:
                best_symlink = output_dir.resolve() / "best_candidate.png"
                try:
                    # Remove existing symlink/file if it exists
                    if best_symlink.exists() or best_symlink.is_symlink():
                        if best_symlink.is_symlink():
                            best_symlink.unlink()
                        else:
                            best_symlink.unlink()
                    
                    # Try to create symlink using absolute path
                    # Use relative path for symlink if both are in same directory tree
                    try:
                        best_symlink.symlink_to(best_path_abs.name)
                    except (OSError, NotImplementedError):
                        # Fallback: use absolute path for symlink
                        best_symlink.symlink_to(best_path_abs)
                    
                    # Verify symlink was created and points to valid file
                    if best_symlink.exists() and best_symlink.resolve().exists():
                        print(f"\n✅ Best candidate marked: {best_symlink.name} → {best_path_abs.name}")
                    else:
                        raise RuntimeError("Symlink created but target not accessible")
                        
                except (OSError, NotImplementedError, RuntimeError) as e:
                    # Fallback: copy file if symlink fails (Windows compatibility or permission issues)
                    import shutil
                    try:
                        # Ensure we copy from absolute path
                        shutil.copy2(best_path_abs, best_symlink)
                        # Verify copy succeeded
                        if best_symlink.exists() and best_symlink.stat().st_size > 0:
                            print(f"\n✅ Best candidate saved: {best_symlink.name}")
                        else:
                            raise RuntimeError("File copy failed or resulted in empty file")
                    except Exception as copy_error:
                        print(f"\n❌ ERROR: Failed to create best candidate file: {copy_error}")
                        print(f"   Best image is still available at: {best_path_abs}")
        
        # Print results
        print_results(final_image_paths, output_dir, trace_data, generation_results)
        
        # Calculate and display elapsed time
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        if minutes > 0:
            print(f"\n⏱️  Total execution time: {minutes}m {seconds}s ({elapsed_time:.2f} seconds)")
        else:
            print(f"\n⏱️  Total execution time: {seconds}s ({elapsed_time:.2f} seconds)")
        
        print("\n✅ Image generation complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def calculate_comparison_summary(best_scores: Dict, other_scores: List[Dict]) -> List[str]:
    """Calculate dynamic comparison showing why top image scored highest."""
    if not other_scores:
        return ["  - This is the only image generated"]
    
    # Calculate averages for other images
    avg_scores = {
        "pickscore": sum(s.get("pickscore", 0) for s in other_scores) / len(other_scores),
        "clip_score": sum(s.get("clip_score", 0) for s in other_scores) / len(other_scores),
        "aesthetic": sum(s.get("aesthetic", 0) for s in other_scores) / len(other_scores),
    }
    
    # Calculate differences
    reasons = []
    
    pickscore_diff = best_scores.get("pickscore", 0) - avg_scores["pickscore"]
    if pickscore_diff > 5:
        reasons.append(f"  • PickScore {pickscore_diff:+.1f} points above average ({best_scores.get('pickscore', 0):.1f} vs {avg_scores['pickscore']:.1f})")
    elif pickscore_diff < -5:
        reasons.append(f"  • PickScore {abs(pickscore_diff):.1f} points below average, but compensated by other metrics")
    
    clip_diff = best_scores.get("clip_score", 0) - avg_scores["clip_score"]
    if clip_diff > 5:
        reasons.append(f"  • CLIP-Score {clip_diff:+.1f} points above average ({best_scores.get('clip_score', 0):.1f} vs {avg_scores['clip_score']:.1f}) - better prompt alignment")
    elif clip_diff < -5:
        reasons.append(f"  • CLIP-Score {abs(clip_diff):.1f} points below average, but compensated by other metrics")
    
    aesthetic_diff = best_scores.get("aesthetic", 0) - avg_scores["aesthetic"]
    if aesthetic_diff > 5:
        reasons.append(f"  • Aesthetic {aesthetic_diff:+.1f} points above average ({best_scores.get('aesthetic', 0):.1f} vs {avg_scores['aesthetic']:.1f}) - more visually appealing")
    
    overall_diff = best_scores.get("overall", 0) - sum(s.get("overall", 0) for s in other_scores) / len(other_scores)
    if overall_diff > 0:
        reasons.append(f"  • Overall score {overall_diff:+.1f} points higher than average")
    
    if not reasons:
        reasons.append("  - Balanced performance across all metrics")
    
    return reasons


def print_results(
    ranked_images: List[tuple],
    output_dir: Path,
    trace_data: Dict,
    generation_results: List = None
):
    """Print generation results to console."""
    print("\n" + "=" * 70)
    print("IMAGE GENERATION RESULTS")
    print("=" * 70)
    
    print(f"\n📊 Generated {len(ranked_images)} images")
    print(f"💰 Total cost: ${trace_data.get('costs', {}).get('total', 0):.4f}")
    if generation_results:
        per_image = trace_data.get('costs', {}).get('per_image', 0)
        if per_image:
            print(f"   Per-image cost: ${per_image:.4f}")
    print(f"📁 Output directory: {output_dir}")
    
    print("\n🏆 RANKED IMAGES (by overall quality score):")
    print("-" * 70)
    
    # Handle both old tuple format (3 elements) and new format (4 elements)
    def unpack_image(item):
        if len(item) == 4:
            image_path, scores, rank, _ = item
        else:
            image_path, scores, rank = item
        return image_path, scores, rank
    
    # Print top 3 highlighted with cost breakdown
    for i, item in enumerate(ranked_images[:3]):
        image_path, scores, rank = unpack_image(item)
        marker = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉"
        print(f"\n{marker} Rank #{rank} (Top {i+1})")
        print(f"   File: {Path(image_path).name}")
        print(f"   Overall Score: {scores['overall']:.1f}/100")
        print(f"   - PickScore:    {scores.get('pickscore', 0):.1f}/100")
        print(f"   - CLIP-Score:   {scores.get('clip_score', 0):.1f}/100")
        if scores.get('vqa_score') is not None:
            print(f"   - VQAScore:     {scores['vqa_score']:.1f}/100")
        print(f"   - Aesthetic:     {scores.get('aesthetic', 0):.1f}/100")
        # Add cost per image if available
        if generation_results and i < len(generation_results):
            print(f"   - Cost:         ${generation_results[i].cost:.4f}")
        print(f"   Path: {image_path}")
    
    # Print remaining images
    if len(ranked_images) > 3:
        print(f"\n📋 Remaining images:")
        for i, item in enumerate(ranked_images[3:], start=3):
            image_path, scores, rank = unpack_image(item)
            cost_str = ""
            if generation_results and i < len(generation_results):
                cost_str = f" (Cost: ${generation_results[i].cost:.4f})"
            print(f"   #{rank}: {Path(image_path).name} (Score: {scores['overall']:.1f}/100){cost_str}")
    
    # Best candidate summary with dynamic comparison
    if ranked_images:
        best_path, best_scores, best_rank = unpack_image(ranked_images[0])
        other_scores = [unpack_image(item)[1] for item in ranked_images[1:]]
        comparison_reasons = calculate_comparison_summary(best_scores, other_scores)
        
        print("\n" + "=" * 70)
        print("BEST CANDIDATE")
        print("=" * 70)
        print(f"Image: {Path(best_path).name}")
        print(f"Overall Score: {best_scores['overall']:.1f}/100")
        print(f"\nScore Breakdown:")
        print(f"  • PickScore (50%):    {best_scores.get('pickscore', 0):.1f}/100")
        print(f"  • CLIP-Score (25%):  {best_scores.get('clip_score', 0):.1f}/100")
        if best_scores.get('vqa_score') is not None:
            print(f"  • VQAScore (15%):    {best_scores['vqa_score']:.1f}/100")
        print(f"  • Aesthetic (10%):   {best_scores.get('aesthetic', 0):.1f}/100")
        print(f"\nWhy this image scored highest:")
        for reason in comparison_reasons:
            print(reason)
        print(f"\nFull path: {best_path}")
    
    print("\n" + "=" * 70)
    print(f"📄 Trace file: {output_dir / 'generation_trace.json'}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

