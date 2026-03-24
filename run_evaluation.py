#!/usr/bin/env python3
"""
Main Evaluation Script for NLP to SQL System
Run comprehensive evaluation with metrics and visualizations
"""

import argparse
import os
import sys
from datetime import datetime

from evaluation_framework import NLPSQLEvaluator
from dataset_generator import DatasetGenerator


def main():
    # Fix Windows console encoding
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    parser = argparse.ArgumentParser(
        description="Run comprehensive evaluation of NLP to SQL system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run evaluation on existing test dataset
  python run_evaluation.py --dataset test_dataset.json

  # Generate new dataset and evaluate
  python run_evaluation.py --generate 100 --dataset generated_test_dataset.json

  # Run evaluation without visualizations
  python run_evaluation.py --dataset test_dataset.json --no-viz

  # Specify output directory
  python run_evaluation.py --dataset test_dataset.json --output my_results
        """
    )

    parser.add_argument(
        '--dataset',
        type=str,
        default='test_dataset.json',
        help='Path to test dataset JSON file (default: test_dataset.json)'
    )

    parser.add_argument(
        '--generate',
        type=int,
        metavar='N',
        help='Generate N synthetic test samples before evaluation'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='evaluation_results',
        help='Output directory for results (default: evaluation_results)'
    )

    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Skip visualization generation'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help='Print detailed progress (default: True)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress detailed output'
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Handle dataset generation if requested
    if args.generate:
        print(f"\n🔄 Generating {args.generate} synthetic test samples...\n")
        generator = DatasetGenerator()

        if os.path.exists(args.dataset):
            # Extend existing dataset
            output_file = f"extended_{args.dataset}"
            generator.extend_existing_dataset(args.dataset, output_file, args.generate)
            args.dataset = output_file
        else:
            # Create new dataset
            samples = generator.generate_samples(args.generate)
            generator.save_dataset(samples, args.dataset)

        print(f"\n✅ Dataset ready: {args.dataset}\n")

    # Check if dataset exists
    if not os.path.exists(args.dataset):
        print(f"\n❌ Error: Dataset file '{args.dataset}' not found!")
        print("\nYou can:")
        print(f"  1. Generate a new dataset: python run_evaluation.py --generate 100")
        print(f"  2. Use the provided test dataset: python run_evaluation.py --dataset test_dataset.json")
        sys.exit(1)

    # Run evaluation
    verbose = args.verbose and not args.quiet
    evaluator = NLPSQLEvaluator(verbose=verbose)

    try:
        print(f"\n🚀 Starting evaluation...\n")

        results = evaluator.run_full_evaluation(
            dataset_path=args.dataset,
            output_dir=args.output,
            generate_viz=not args.no_viz
        )

        # Print final message
        print(f"\n{'='*70}")
        print(f"✅ EVALUATION COMPLETE!")
        print(f"{'='*70}")
        print(f"\n📁 Results saved to: {os.path.abspath(args.output)}")
        print(f"\n📊 Key Metrics:")
        print(f"   BLEU Score:         {results['overall_metrics'].get('avg_bleu', 0):.4f}")
        print(f"   Exact Match Rate:   {results['summary']['exact_match_rate']*100:.2f}%")
        print(f"   Success Rate:       {results['summary']['success_rate']*100:.2f}%")
        print()

        if not args.no_viz:
            print(f"📊 Visualizations:")
            print(f"   - overall_metrics.png")
            print(f"   - component_accuracy.png")
            print(f"   - category_performance.png")
            print(f"   - difficulty_performance.png")
            print(f"   - comprehensive_dashboard.png")
            print()

        print(f"📄 Files generated:")
        print(f"   - evaluation_results.json (detailed results)")
        print(f"   - evaluation_summary.txt (summary report)")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user.")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              NLP TO SQL EVALUATION SYSTEM                            ║
║                                                                      ║
║              Comprehensive Evaluation with:                          ║
║              • BLEU, ROUGE, and Exact Match Metrics                  ║
║              • Component-wise Accuracy Analysis                      ║
║              • Interactive Visualizations & Charts                   ║
║              • Detailed Performance Reports                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def quick_test():
    """Run a quick test with a few samples"""
    print("🧪 Running quick test with sample queries...\n")

    from interactive_nlp_extractor import NLPExtractor
    from interactive_query_processor import QueryProcessor
    from evaluation_metrics import EvaluationMetrics

    extractor = NLPExtractor()
    processor = QueryProcessor()
    metrics_calc = EvaluationMetrics()

    test_queries = [
        ("Show all students", "SELECT * FROM students;"),
        ("Top 10 students with highest CGPA", "SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;"),
        ("Average salary of employees", "SELECT AVG(salary) as result FROM employees;"),
    ]

    print(f"{'Query':<40} {'BLEU':<8} {'Exact':<8}")
    print("-" * 60)

    for nl, expected in test_queries:
        keywords = extractor.extract_keywords(nl)
        generated = processor.process(keywords)
        metrics = metrics_calc.calculate_all(expected, generated)

        bleu = metrics.get('bleu', 0)
        exact = metrics.get('exact_match', 0)

        print(f"{nl:<40} {bleu:<8.3f} {exact:<8.0f}")

    print("\n✅ Quick test complete!\n")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, show help
        print_banner()
        print("\nNo arguments provided. Use --help for usage information.")
        print("\nQuick start:")
        print("  python run_evaluation.py --dataset test_dataset.json")
        print("  python run_evaluation.py --generate 100")
        print()
    else:
        main()
