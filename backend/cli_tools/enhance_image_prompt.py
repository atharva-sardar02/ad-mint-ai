#!/usr/bin/env python3
"""
Standalone CLI tool for image prompt enhancement.

Usage:
    python enhance_image_prompt.py <input_file> [--output-dir <dir>] [--max-iterations <n>] [--threshold <score>]

Examples:
    # Basic usage - reads from prompt.txt, saves to output/image_prompt_traces/
    python enhance_image_prompt.py prompt.txt

    # Custom output directory
    python enhance_image_prompt.py prompt.txt --output-dir ./my_traces

    # Custom iteration settings
    python enhance_image_prompt.py prompt.txt --max-iterations 5 --threshold 90

    # Read from stdin
    echo "A cat in a city" | python enhance_image_prompt.py -
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pipeline.image_prompt_enhancement import enhance_prompt_iterative
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


def print_results(result, output_dir: Path):
    """Print enhancement results to console."""
    print("\n" + "=" * 70)
    print("IMAGE PROMPT ENHANCEMENT RESULTS")
    print("=" * 70)
    
    print(f"\n📊 Final Score: {result.final_score['overall']:.1f}/100")
    print(f"   Completeness:    {result.final_score['completeness']:.1f}/100")
    print(f"   Specificity:     {result.final_score['specificity']:.1f}/100")
    print(f"   Professionalism: {result.final_score['professionalism']:.1f}/100")
    print(f"   Cinematography:  {result.final_score['cinematography']:.1f}/100")
    print(f"   Brand Alignment: {result.final_score['brand_alignment']:.1f}/100")
    
    print(f"\n🔄 Total Iterations: {result.total_iterations}")
    
    if result.iterations:
        print("\n📝 Iteration History:")
        for i, iteration in enumerate(result.iterations, 1):
            print(f"\n   Iteration {i}:")
            print(f"   - Score: {iteration['scores']['overall']:.1f}/100")
            print(f"   - Key Improvements: {', '.join(iteration['improvements'][:2])}")
    
    print(f"\n📁 Trace files saved to: {output_dir}")
    print(f"   - Original prompt: 00_original_prompt.txt")
    print(f"   - Final prompt: 05_final_enhanced_prompt.txt")
    print(f"   - Summary: prompt_trace_summary.json")
    
    print("\n" + "=" * 70)
    print("FINAL ENHANCED PROMPT")
    print("=" * 70)
    print(result.final_prompt)
    print("=" * 70)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enhance image prompts using two-agent iterative refinement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "input",
        help="Input file path or '-' for stdin"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for trace files (default: output/image_prompt_traces/<timestamp>)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum iteration rounds (default: 3)"
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
        help="Model for Cinematographer agent (default: gpt-4-turbo)"
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
        # Load prompt
        print(f"📖 Loading prompt from: {args.input if args.input != '-' else 'stdin'}")
        original_prompt = load_prompt(args.input)
        print(f"✓ Loaded prompt ({len(original_prompt)} characters)")
        
        # Setup output directory
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output") / "image_prompt_traces" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {output_dir}")
        print(f"\n🚀 Starting image prompt enhancement...")
        print(f"   Max iterations: {args.max_iterations}")
        print(f"   Score threshold: {args.threshold}")
        print(f"   Creative model: {args.creative_model}")
        print(f"   Critique model: {args.critique_model}")
        
        # Run enhancement
        result = await enhance_prompt_iterative(
            user_prompt=original_prompt,
            max_iterations=args.max_iterations,
            score_threshold=args.threshold,
            creative_model=args.creative_model,
            critique_model=args.critique_model,
            trace_dir=output_dir
        )
        
        # Print results
        print_results(result, output_dir)
        
        # Save final prompt to a convenient location
        final_prompt_file = output_dir / "FINAL_PROMPT.txt"
        final_prompt_file.write_text(result.final_prompt, encoding="utf-8")
        print(f"\n✓ Final prompt also saved to: {final_prompt_file}")
        
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

