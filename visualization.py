"""
Visualization Module for NLP to SQL Evaluation
Creates charts, plots, and dashboards for metrics visualization
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class MetricsVisualizer:
    """Create visualizations for evaluation metrics"""

    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """Initialize visualizer with matplotlib style"""
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')

        # Color schemes
        self.colors = {
            'primary': '#2ecc71',
            'secondary': '#3498db',
            'accent': '#e74c3c',
            'warning': '#f39c12',
            'success': '#27ae60',
            'info': '#3498db',
            'dark': '#34495e',
            'light': '#ecf0f1'
        }

        self.metric_colors = {
            'bleu': '#3498db',
            'rouge': '#e74c3c',
            'exact_match': '#2ecc71',
            'similarity': '#9b59b6',
            'component': '#f39c12'
        }

    def plot_metric_comparison(
        self,
        metrics: Dict[str, float],
        title: str = "Evaluation Metrics",
        save_path: Optional[str] = None
    ):
        """
        Create bar chart comparing different metrics

        Args:
            metrics: Dictionary of metric names and values
            title: Chart title
            save_path: Path to save figure (optional)
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Filter metrics to show (main ones)
        main_metrics = {
            'BLEU': metrics.get('avg_bleu', 0),
            'ROUGE-1 F1': metrics.get('avg_rouge_1_f1', 0),
            'ROUGE-2 F1': metrics.get('avg_rouge_2_f1', 0),
            'ROUGE-L F1': metrics.get('avg_rouge_l_f1', 0),
            'Exact Match': metrics.get('avg_exact_match', 0),
            'Similarity': metrics.get('avg_similarity_ratio', 0),
            'Component Acc': metrics.get('avg_overall_component_accuracy', 0)
        }

        # Remove None values
        main_metrics = {k: v for k, v in main_metrics.items() if v is not None}

        names = list(main_metrics.keys())
        values = list(main_metrics.values())

        # Create bars with colors
        colors = [self.metric_colors.get('bleu', '#3498db') if 'BLEU' in name else
                  self.metric_colors.get('rouge', '#e74c3c') if 'ROUGE' in name else
                  self.metric_colors.get('exact_match', '#2ecc71') if 'Exact' in name else
                  self.metric_colors.get('similarity', '#9b59b6') if 'Similarity' in name else
                  self.metric_colors.get('component', '#f39c12')
                  for name in names]

        bars = ax.bar(names, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}\n({height*100:.1f}%)',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_ylim(0, 1.1)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Saved chart to {save_path}")

        plt.show()

    def plot_component_accuracy(
        self,
        metrics: Dict[str, float],
        title: str = "Component-wise Accuracy",
        save_path: Optional[str] = None
    ):
        """
        Create bar chart for component-wise accuracy

        Args:
            metrics: Dictionary of metrics
            title: Chart title
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract component accuracies
        component_metrics = {
            'SELECT': metrics.get('avg_select_accuracy', 0),
            'FROM': metrics.get('avg_from_accuracy', 0),
            'WHERE': metrics.get('avg_where_accuracy', 0),
            'ORDER BY': metrics.get('avg_order_by_accuracy', 0),
            'LIMIT': metrics.get('avg_limit_accuracy', 0),
            'Aggregation': metrics.get('avg_aggregation_accuracy', 0),
        }

        # Remove None values
        component_metrics = {k: v for k, v in component_metrics.items() if v is not None}

        names = list(component_metrics.keys())
        values = list(component_metrics.values())

        # Color based on accuracy
        colors = ['#27ae60' if v >= 0.8 else '#f39c12' if v >= 0.5 else '#e74c3c' for v in values]

        bars = ax.barh(names, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, values)):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {value:.3f} ({value*100:.1f}%)',
                   ha='left', va='center', fontsize=11, fontweight='bold')

        ax.set_xlabel('Accuracy', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlim(0, 1.1)
        ax.grid(axis='x', alpha=0.3, linestyle='--')

        # Add legend
        green_patch = mpatches.Patch(color='#27ae60', label='Good (≥80%)')
        yellow_patch = mpatches.Patch(color='#f39c12', label='Fair (50-80%)')
        red_patch = mpatches.Patch(color='#e74c3c', label='Poor (<50%)')
        ax.legend(handles=[green_patch, yellow_patch, red_patch], loc='lower right')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Saved chart to {save_path}")

        plt.show()

    def plot_category_performance(
        self,
        results_by_category: Dict[str, Dict[str, float]],
        title: str = "Performance by Query Category",
        save_path: Optional[str] = None
    ):
        """
        Create grouped bar chart for performance across categories

        Args:
            results_by_category: Dict mapping category to metrics dict
            title: Chart title
            save_path: Path to save figure
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        categories = list(results_by_category.keys())
        metrics_to_plot = ['avg_bleu', 'avg_rouge_1_f1', 'avg_exact_match', 'avg_overall_component_accuracy']
        metric_labels = ['BLEU', 'ROUGE-1', 'Exact Match', 'Component Acc']

        x = np.arange(len(categories))
        width = 0.2

        for i, (metric, label) in enumerate(zip(metrics_to_plot, metric_labels)):
            values = [results_by_category[cat].get(metric, 0) for cat in categories]
            offset = (i - len(metrics_to_plot)/2) * width + width/2
            ax.bar(x + offset, values, width, label=label, alpha=0.8, edgecolor='black', linewidth=0.8)

        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_ylim(0, 1.1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Saved chart to {save_path}")

        plt.show()

    def plot_difficulty_performance(
        self,
        results_by_difficulty: Dict[str, Dict[str, float]],
        title: str = "Performance by Query Difficulty",
        save_path: Optional[str] = None
    ):
        """Create visualization for performance across difficulty levels"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        difficulties = ['easy', 'medium', 'hard']
        colors_diff = ['#27ae60', '#f39c12', '#e74c3c']

        # Plot 1: Main metrics
        metrics = ['avg_bleu', 'avg_rouge_1_f1', 'avg_exact_match']
        metric_labels = ['BLEU', 'ROUGE-1 F1', 'Exact Match']

        x = np.arange(len(difficulties))
        width = 0.25

        for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
            values = [results_by_difficulty.get(diff, {}).get(metric, 0) for diff in difficulties]
            ax1.bar(x + i*width, values, width, label=label, alpha=0.8, edgecolor='black', linewidth=0.8)

        ax1.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax1.set_title('Main Metrics by Difficulty', fontsize=12, fontweight='bold')
        ax1.set_xticks(x + width)
        ax1.set_xticklabels([d.capitalize() for d in difficulties])
        ax1.legend(fontsize=10)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.set_ylim(0, 1.1)

        # Plot 2: Component accuracy
        values = [results_by_difficulty.get(diff, {}).get('avg_overall_component_accuracy', 0) for diff in difficulties]
        bars = ax2.bar(difficulties, values, color=colors_diff, alpha=0.8, edgecolor='black', linewidth=1.2)

        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.3f}\n({value*100:.1f}%)',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax2.set_ylabel('Component Accuracy', fontsize=12, fontweight='bold')
        ax2.set_title('Component Accuracy by Difficulty', fontsize=12, fontweight='bold')
        ax2.set_xticks(range(len(difficulties)))
        ax2.set_xticklabels([d.capitalize() for d in difficulties])
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        ax2.set_ylim(0, 1.1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Saved chart to {save_path}")

        plt.show()

    def create_comprehensive_dashboard(
        self,
        overall_metrics: Dict[str, float],
        category_results: Dict[str, Dict[str, float]],
        difficulty_results: Dict[str, Dict[str, float]],
        save_path: Optional[str] = None
    ):
        """
        Create comprehensive dashboard with multiple visualizations

        Args:
            overall_metrics: Overall aggregated metrics
            category_results: Results broken down by category
            difficulty_results: Results broken down by difficulty
            save_path: Path to save figure
        """
        fig = plt.figure(figsize=(18, 12))
        gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

        # Overall metrics comparison
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_overall_metrics_on_ax(ax1, overall_metrics)

        # Component accuracy
        ax2 = fig.add_subplot(gs[1, 0])
        self._plot_component_accuracy_on_ax(ax2, overall_metrics)

        # Category performance
        ax3 = fig.add_subplot(gs[1, 1])
        self._plot_category_summary_on_ax(ax3, category_results)

        # Difficulty performance
        ax4 = fig.add_subplot(gs[2, 0])
        self._plot_difficulty_summary_on_ax(ax4, difficulty_results)

        # Metric trends (BLEU vs ROUGE vs Exact Match) - radar chart needs polar projection
        ax5 = fig.add_subplot(gs[2, 1], projection='polar')
        self._plot_metric_relationships_on_ax(ax5, overall_metrics)

        # Main title
        fig.suptitle('NLP to SQL Evaluation Dashboard', fontsize=18, fontweight='bold', y=0.995)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Saved dashboard to {save_path}")

        plt.show()

    def _plot_overall_metrics_on_ax(self, ax, metrics: Dict[str, float]):
        """Plot overall metrics on given axis"""
        main_metrics = {
            'BLEU': metrics.get('avg_bleu', 0),
            'ROUGE-1': metrics.get('avg_rouge_1_f1', 0),
            'ROUGE-L': metrics.get('avg_rouge_l_f1', 0),
            'Exact Match': metrics.get('avg_exact_match', 0),
            'Similarity': metrics.get('avg_similarity_ratio', 0),
            'Component': metrics.get('avg_overall_component_accuracy', 0)
        }

        main_metrics = {k: v for k, v in main_metrics.items() if v is not None}
        names = list(main_metrics.keys())
        values = list(main_metrics.values())

        colors = ['#3498db', '#e74c3c', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12']
        bars = ax.bar(names, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

        ax.set_ylabel('Score', fontsize=11, fontweight='bold')
        ax.set_title('Overall Evaluation Metrics', fontsize=12, fontweight='bold')
        ax.set_ylim(0, 1.1)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

    def _plot_component_accuracy_on_ax(self, ax, metrics: Dict[str, float]):
        """Plot component accuracy on given axis"""
        component_metrics = {
            'SELECT': metrics.get('avg_select_accuracy', 0),
            'FROM': metrics.get('avg_from_accuracy', 0),
            'WHERE': metrics.get('avg_where_accuracy', 0),
            'ORDER BY': metrics.get('avg_order_by_accuracy', 0),
            'LIMIT': metrics.get('avg_limit_accuracy', 0),
        }

        component_metrics = {k: v for k, v in component_metrics.items() if v is not None}
        names = list(component_metrics.keys())
        values = list(component_metrics.values())

        colors = ['#27ae60' if v >= 0.8 else '#f39c12' if v >= 0.5 else '#e74c3c' for v in values]
        bars = ax.barh(names, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {value:.2f}',
                   ha='left', va='center', fontsize=9, fontweight='bold')

        ax.set_xlabel('Accuracy', fontsize=11, fontweight='bold')
        ax.set_title('Component-wise Accuracy', fontsize=12, fontweight='bold')
        ax.set_xlim(0, 1.1)
        ax.grid(axis='x', alpha=0.3, linestyle='--')

    def _plot_category_summary_on_ax(self, ax, category_results: Dict[str, Dict[str, float]]):
        """Plot category summary on given axis"""
        categories = list(category_results.keys())
        bleu_scores = [category_results[cat].get('avg_bleu', 0) for cat in categories]

        ax.barh(categories, bleu_scores, color='#3498db', alpha=0.8, edgecolor='black', linewidth=1.2)

        for i, value in enumerate(bleu_scores):
            ax.text(value, i, f' {value:.3f}', ha='left', va='center', fontsize=9, fontweight='bold')

        ax.set_xlabel('BLEU Score', fontsize=11, fontweight='bold')
        ax.set_title('BLEU Score by Category', fontsize=12, fontweight='bold')
        ax.set_xlim(0, 1.1)
        ax.grid(axis='x', alpha=0.3, linestyle='--')

    def _plot_difficulty_summary_on_ax(self, ax, difficulty_results: Dict[str, Dict[str, float]]):
        """Plot difficulty summary on given axis"""
        difficulties = ['easy', 'medium', 'hard']
        colors = ['#27ae60', '#f39c12', '#e74c3c']

        exact_match = [difficulty_results.get(d, {}).get('avg_exact_match', 0) for d in difficulties]

        bars = ax.bar(difficulties, exact_match, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

        for bar, value in zip(bars, exact_match):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.3f}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

        ax.set_ylabel('Exact Match', fontsize=11, fontweight='bold')
        ax.set_title('Exact Match by Difficulty', fontsize=12, fontweight='bold')
        ax.set_xticks(range(len(difficulties)))
        ax.set_xticklabels([d.capitalize() for d in difficulties])
        ax.set_ylim(0, 1.1)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

    def _plot_metric_relationships_on_ax(self, ax, metrics: Dict[str, float]):
        """Plot metric relationships as radar/spider chart"""
        categories = ['BLEU', 'ROUGE-1', 'ROUGE-L', 'Exact\nMatch', 'Similarity', 'Component']
        values = [
            metrics.get('avg_bleu', 0),
            metrics.get('avg_rouge_1_f1', 0),
            metrics.get('avg_rouge_l_f1', 0),
            metrics.get('avg_exact_match', 0),
            metrics.get('avg_similarity_ratio', 0),
            metrics.get('avg_overall_component_accuracy', 0)
        ]

        # Number of variables
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        values += values[:1]
        angles += angles[:1]

        # Use the provided ax which is already polar projection
        ax.plot(angles, values, 'o-', linewidth=2, color='#3498db', label='Metrics')
        ax.fill(angles, values, alpha=0.25, color='#3498db')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=9)
        ax.set_ylim(0, 1)
        ax.set_title('Metric Radar Chart', fontsize=12, fontweight='bold', pad=20)
        ax.grid(True)


def save_results_json(results: Dict[str, Any], filename: str):
    """Save evaluation results to JSON file"""
    results['timestamp'] = datetime.now().isoformat()

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved results to {filename}")


if __name__ == "__main__":
    # Test visualization with dummy data
    print("Testing MetricsVisualizer...\n")

    viz = MetricsVisualizer()

    # Dummy overall metrics
    overall_metrics = {
        'avg_bleu': 0.85,
        'avg_rouge_1_f1': 0.90,
        'avg_rouge_2_f1': 0.82,
        'avg_rouge_l_f1': 0.88,
        'avg_exact_match': 0.75,
        'avg_similarity_ratio': 0.92,
        'avg_overall_component_accuracy': 0.87,
        'avg_select_accuracy': 0.95,
        'avg_from_accuracy': 0.98,
        'avg_where_accuracy': 0.80,
        'avg_order_by_accuracy': 0.85,
        'avg_limit_accuracy': 0.90,
    }

    # Test individual plots
    viz.plot_metric_comparison(overall_metrics, save_path='test_metrics.png')
    viz.plot_component_accuracy(overall_metrics, save_path='test_components.png')

    print("✅ Visualization test complete!")
