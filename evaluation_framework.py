"""
Comprehensive Evaluation Framework for NLP to SQL System
Orchestrates end-to-end evaluation with metrics and visualizations
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import traceback

from interactive_nlp_extractor import NLPExtractor
from interactive_query_processor import QueryProcessor
from evaluation_metrics import EvaluationMetrics
from visualization import MetricsVisualizer, save_results_json


class NLPSQLEvaluator:
    """Main evaluation framework for NLP to SQL system"""

    def __init__(self, verbose: bool = True):
        """
        Initialize evaluator

        Args:
            verbose: Print detailed progress information
        """
        self.verbose = verbose
        self.extractor = NLPExtractor()
        self.processor = QueryProcessor()
        self.metrics_calculator = EvaluationMetrics()
        self.visualizer = MetricsVisualizer()

    def evaluate_single(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single test case

        Args:
            test_case: Test case dictionary with natural_language and expected_sql

        Returns:
            Dictionary with generated SQL, metrics, and status
        """
        try:
            nl_query = test_case['natural_language']
            expected_sql = test_case['expected_sql']

            # Step 1: Extract keywords
            keywords = self.extractor.extract_keywords(nl_query)

            # Step 2: Generate SQL
            generated_sql = self.processor.process(keywords)

            # Step 3: Calculate metrics
            metrics = self.metrics_calculator.calculate_all(expected_sql, generated_sql)

            result = {
                'test_id': test_case.get('id'),
                'category': test_case.get('category'),
                'difficulty': test_case.get('difficulty'),
                'natural_language': nl_query,
                'expected_sql': expected_sql,
                'generated_sql': generated_sql,
                'keywords': keywords,
                'metrics': metrics,
                'status': 'success'
            }

            if self.verbose:
                exact_match = metrics.get('exact_match', 0)
                status_symbol = '✓' if exact_match == 1.0 else '⚠'
                print(f"{status_symbol} Test {test_case.get('id')}: BLEU={metrics.get('bleu', 0):.3f}, "
                      f"Exact={exact_match:.0f}, Category={test_case.get('category')}")

            return result

        except Exception as e:
            error_msg = str(e)
            if self.verbose:
                print(f"✗ Test {test_case.get('id')} FAILED: {error_msg}")

            return {
                'test_id': test_case.get('id'),
                'category': test_case.get('category'),
                'difficulty': test_case.get('difficulty'),
                'natural_language': test_case.get('natural_language'),
                'expected_sql': test_case.get('expected_sql'),
                'generated_sql': None,
                'error': error_msg,
                'status': 'error'
            }

    def evaluate_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """
        Evaluate entire dataset

        Args:
            dataset_path: Path to JSON dataset file

        Returns:
            Dictionary with all results and aggregated metrics
        """
        print(f"\n{'='*70}")
        print(f"Starting Evaluation: {dataset_path}")
        print(f"{'='*70}\n")

        # Load dataset
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        test_cases = dataset.get('test_cases', [])
        print(f"📊 Total test cases: {len(test_cases)}\n")

        # Evaluate all test cases
        results = []
        for i, test_case in enumerate(test_cases):
            if self.verbose and i % 10 == 0:
                print(f"\nProgress: {i}/{len(test_cases)} ({i/len(test_cases)*100:.1f}%)")

            result = self.evaluate_single(test_case)
            results.append(result)

        print(f"\n{'='*70}")
        print("Evaluation Complete!")
        print(f"{'='*70}\n")

        # Calculate aggregated metrics
        aggregated_metrics = self._aggregate_results(results)

        # Breakdown by category
        category_results = self._breakdown_by_category(results)

        # Breakdown by difficulty
        difficulty_results = self._breakdown_by_difficulty(results)

        # Summary statistics
        summary = self._calculate_summary(results)

        evaluation_results = {
            'metadata': {
                'dataset_path': dataset_path,
                'total_test_cases': len(test_cases),
                'timestamp': datetime.now().isoformat(),
                'successful_tests': summary['successful_tests'],
                'failed_tests': summary['failed_tests'],
            },
            'overall_metrics': aggregated_metrics,
            'category_breakdown': category_results,
            'difficulty_breakdown': difficulty_results,
            'summary': summary,
            'detailed_results': results
        }

        return evaluation_results

    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate metrics across all test cases"""
        successful_results = [r for r in results if r['status'] == 'success']

        if not successful_results:
            return {}

        all_metrics = [r['metrics'] for r in successful_results]
        aggregated = self.metrics_calculator.aggregate_results(all_metrics)

        return aggregated

    def _breakdown_by_category(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Break down results by query category"""
        categories = {}

        for result in results:
            if result['status'] != 'success':
                continue

            category = result.get('category', 'unknown')
            if category not in categories:
                categories[category] = []

            categories[category].append(result['metrics'])

        # Aggregate by category
        category_results = {}
        for category, metrics_list in categories.items():
            category_results[category] = self.metrics_calculator.aggregate_results(metrics_list)

        return category_results

    def _breakdown_by_difficulty(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Break down results by difficulty level"""
        difficulties = {}

        for result in results:
            if result['status'] != 'success':
                continue

            difficulty = result.get('difficulty', 'unknown')
            if difficulty not in difficulties:
                difficulties[difficulty] = []

            difficulties[difficulty].append(result['metrics'])

        # Aggregate by difficulty
        difficulty_results = {}
        for difficulty, metrics_list in difficulties.items():
            difficulty_results[difficulty] = self.metrics_calculator.aggregate_results(metrics_list)

        return difficulty_results

    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        total = len(results)
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'error')

        # Count exact matches
        exact_matches = sum(1 for r in results if r['status'] == 'success' and
                          r['metrics'].get('exact_match', 0) == 1.0)

        # Count high-quality results (BLEU > 0.8)
        high_quality = sum(1 for r in results if r['status'] == 'success' and
                          r['metrics'].get('bleu', 0) >= 0.8)

        return {
            'total_test_cases': total,
            'successful_tests': successful,
            'failed_tests': failed,
            'exact_matches': exact_matches,
            'exact_match_rate': exact_matches / successful if successful > 0 else 0,
            'high_quality_results': high_quality,
            'high_quality_rate': high_quality / successful if successful > 0 else 0,
            'success_rate': successful / total if total > 0 else 0
        }

    def print_summary(self, evaluation_results: Dict[str, Any]):
        """Print evaluation summary"""
        print(f"\n{'='*70}")
        print(f"{'EVALUATION SUMMARY':^70}")
        print(f"{'='*70}\n")

        summary = evaluation_results['summary']
        overall = evaluation_results['overall_metrics']

        print("📊 Test Statistics:")
        print(f"  Total Test Cases:       {summary['total_test_cases']}")
        print(f"  Successful Tests:       {summary['successful_tests']} ({summary['success_rate']*100:.1f}%)")
        print(f"  Failed Tests:           {summary['failed_tests']}")
        print(f"  Exact Matches:          {summary['exact_matches']} ({summary['exact_match_rate']*100:.1f}%)")
        print(f"  High Quality (BLEU>0.8): {summary['high_quality_results']} ({summary['high_quality_rate']*100:.1f}%)")

        print("\n📈 Overall Metrics:")
        print(f"  BLEU Score:             {overall.get('avg_bleu', 0):.4f} ({overall.get('avg_bleu', 0)*100:.2f}%)")
        print(f"  ROUGE-1 F1:             {overall.get('avg_rouge_1_f1', 0):.4f} ({overall.get('avg_rouge_1_f1', 0)*100:.2f}%)")
        print(f"  ROUGE-L F1:             {overall.get('avg_rouge_l_f1', 0):.4f} ({overall.get('avg_rouge_l_f1', 0)*100:.2f}%)")
        print(f"  Exact Match:            {overall.get('avg_exact_match', 0):.4f} ({overall.get('avg_exact_match', 0)*100:.2f}%)")
        print(f"  Similarity Ratio:       {overall.get('avg_similarity_ratio', 0):.4f} ({overall.get('avg_similarity_ratio', 0)*100:.2f}%)")
        print(f"  Component Accuracy:     {overall.get('avg_overall_component_accuracy', 0):.4f} ({overall.get('avg_overall_component_accuracy', 0)*100:.2f}%)")

        print("\n🎯 Component-wise Accuracy:")
        select_acc = overall.get('avg_select_accuracy', 0) or 0
        from_acc = overall.get('avg_from_accuracy', 0) or 0
        where_acc = overall.get('avg_where_accuracy', 0) or 0
        order_acc = overall.get('avg_order_by_accuracy', 0) or 0
        limit_acc = overall.get('avg_limit_accuracy', 0) or 0

        print(f"  SELECT clause:          {select_acc:.4f} ({select_acc*100:.2f}%)")
        print(f"  FROM clause:            {from_acc:.4f} ({from_acc*100:.2f}%)")
        if where_acc > 0:
            print(f"  WHERE clause:           {where_acc:.4f} ({where_acc*100:.2f}%)")
        if order_acc > 0:
            print(f"  ORDER BY clause:        {order_acc:.4f} ({order_acc*100:.2f}%)")
        if limit_acc > 0:
            print(f"  LIMIT clause:           {limit_acc:.4f} ({limit_acc*100:.2f}%)")

        print("\n📂 Performance by Category:")
        for category, metrics in evaluation_results['category_breakdown'].items():
            bleu = metrics.get('avg_bleu', 0)
            exact = metrics.get('avg_exact_match', 0)
            print(f"  {category:30s}: BLEU={bleu:.3f}, Exact Match={exact:.3f}")

        print("\n⚡ Performance by Difficulty:")
        for difficulty, metrics in evaluation_results['difficulty_breakdown'].items():
            bleu = metrics.get('avg_bleu', 0)
            exact = metrics.get('avg_exact_match', 0)
            print(f"  {difficulty.capitalize():30s}: BLEU={bleu:.3f}, Exact Match={exact:.3f}")

        print(f"\n{'='*70}\n")

    def generate_visualizations(
        self,
        evaluation_results: Dict[str, Any],
        output_dir: str = 'evaluation_results'
    ):
        """
        Generate all visualization charts

        Args:
            evaluation_results: Results from evaluate_dataset
            output_dir: Directory to save charts
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n📊 Generating visualizations in '{output_dir}'...\n")

        # 1. Overall metrics comparison
        self.visualizer.plot_metric_comparison(
            evaluation_results['overall_metrics'],
            title="Overall Evaluation Metrics",
            save_path=os.path.join(output_dir, 'overall_metrics.png')
        )

        # 2. Component accuracy
        self.visualizer.plot_component_accuracy(
            evaluation_results['overall_metrics'],
            title="Component-wise Accuracy",
            save_path=os.path.join(output_dir, 'component_accuracy.png')
        )

        # 3. Category performance
        self.visualizer.plot_category_performance(
            evaluation_results['category_breakdown'],
            title="Performance by Query Category",
            save_path=os.path.join(output_dir, 'category_performance.png')
        )

        # 4. Difficulty performance
        self.visualizer.plot_difficulty_performance(
            evaluation_results['difficulty_breakdown'],
            title="Performance by Query Difficulty",
            save_path=os.path.join(output_dir, 'difficulty_performance.png')
        )

        # 5. Comprehensive dashboard
        self.visualizer.create_comprehensive_dashboard(
            evaluation_results['overall_metrics'],
            evaluation_results['category_breakdown'],
            evaluation_results['difficulty_breakdown'],
            save_path=os.path.join(output_dir, 'comprehensive_dashboard.png')
        )

        print(f"\n✅ All visualizations saved to '{output_dir}'\n")

    def save_results(
        self,
        evaluation_results: Dict[str, Any],
        output_dir: str = 'evaluation_results'
    ):
        """
        Save evaluation results to files

        Args:
            evaluation_results: Results from evaluate_dataset
            output_dir: Directory to save results
        """
        os.makedirs(output_dir, exist_ok=True)

        # Save full results as JSON
        results_path = os.path.join(output_dir, 'evaluation_results.json')
        save_results_json(evaluation_results, results_path)

        # Save summary as text
        summary_path = os.path.join(output_dir, 'evaluation_summary.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("NLP to SQL Evaluation Summary\n")
            f.write("=" * 70 + "\n\n")

            summary = evaluation_results['summary']
            overall = evaluation_results['overall_metrics']

            f.write(f"Timestamp: {evaluation_results['metadata']['timestamp']}\n")
            f.write(f"Dataset: {evaluation_results['metadata']['dataset_path']}\n\n")

            f.write("Test Statistics:\n")
            f.write(f"  Total: {summary['total_test_cases']}\n")
            f.write(f"  Successful: {summary['successful_tests']} ({summary['success_rate']*100:.1f}%)\n")
            f.write(f"  Exact Matches: {summary['exact_matches']} ({summary['exact_match_rate']*100:.1f}%)\n\n")

            f.write("Overall Metrics:\n")
            f.write(f"  BLEU: {overall.get('avg_bleu', 0):.4f}\n")
            f.write(f"  ROUGE-1 F1: {overall.get('avg_rouge_1_f1', 0):.4f}\n")
            f.write(f"  Exact Match: {overall.get('avg_exact_match', 0):.4f}\n")
            f.write(f"  Component Accuracy: {overall.get('avg_overall_component_accuracy', 0):.4f}\n")

        print(f"💾 Saved summary to '{summary_path}'")

    def run_full_evaluation(
        self,
        dataset_path: str,
        output_dir: str = 'evaluation_results',
        generate_viz: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete evaluation pipeline

        Args:
            dataset_path: Path to test dataset
            output_dir: Directory for outputs
            generate_viz: Whether to generate visualizations

        Returns:
            Evaluation results dictionary
        """
        # Run evaluation
        results = self.evaluate_dataset(dataset_path)

        # Print summary
        self.print_summary(results)

        # Save results
        self.save_results(results, output_dir)

        # Generate visualizations
        if generate_viz:
            self.generate_visualizations(results, output_dir)

        print(f"\n🎉 Evaluation complete! Results saved to '{output_dir}'\n")

        return results


if __name__ == "__main__":
    # Example usage
    evaluator = NLPSQLEvaluator(verbose=True)

    # Check if test dataset exists
    if os.path.exists('test_dataset.json'):
        print("Running evaluation on test_dataset.json...")
        results = evaluator.run_full_evaluation(
            dataset_path='test_dataset.json',
            output_dir='evaluation_results',
            generate_viz=True
        )
    else:
        print("Error: test_dataset.json not found!")
        print("Please run dataset_generator.py first to create test data.")
