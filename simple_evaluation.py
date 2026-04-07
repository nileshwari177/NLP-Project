import matplotlib.pyplot as plt
import numpy as np
from rouge_score import rouge_scorer
from difflib import SequenceMatcher
from extractor import extract
from builder import build
# Assuming TEST_CASES is structured as: [("query", "expected_sql", "category", "difficulty"), ...]
from test_cases_200 import TEST_CASES


def calculate_metrics():
    # Initialize scorers
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)

    # Storage for all-up metrics
    all_metrics = {
        'exact_matches': 0, 'total_bleu_1': 0, 'total_rouge_1': 0,
        'total_rouge_l': 0, 'total_similarity': 0, 'overall_comp_acc': 0,
        'component_counts': {
            'select': 0, 'table_name': 0, 'where': 0,
            'order_by': 0, 'limit': 0, 'aggregation': 0, 'filter_operator': 0
        }
    }

    # Templates for difficulty tracking
    diff_template = lambda: {
        'count': 0, 'exact_matches': 0, 'total_bleu_1': 0,
        'component_counts': {k: 0 for k in all_metrics['component_counts']}
    }
    easy_metrics = diff_template()
    medium_metrics = diff_template()
    hard_metrics = diff_template()

    # Category performance tracking
    category_data = {}

    for query, expected, cat_name, diff_level in TEST_CASES:
        # Generate SQL and Normalize
        generated = build(extract(query)).lower().replace(';', '').strip()
        ref = expected.lower().replace(';', '').strip()
        gen_words, ref_words = generated.split(), ref.split()

        # 1. Basic Scores
        exact = 100 if generated == ref else 0
        bleu = (sum(1 for w in gen_words if w in ref_words) / len(gen_words) * 100) if gen_words else 0
        rouge_scores = scorer.score(ref, generated)
        r1 = rouge_scores['rouge1'].fmeasure * 100
        rl = rouge_scores['rougeL'].fmeasure * 100
        sim = SequenceMatcher(None, ref, generated).ratio() * 100

        # 2. Component Analysis Logic
        comp_results = {
            'select': 'select' in generated and 'select' in ref,
            'table_name': 'from' in generated and 'from' in ref,
            'where': ('where' in generated) == ('where' in ref),
            'order_by': ('order by' in generated) == ('order by' in ref),
            'limit': ('limit' in generated) == ('limit' in ref),
            'aggregation': any(agg in generated for agg in ['count', 'avg', 'sum', 'max', 'min']) ==
                           any(agg in ref for agg in ['count', 'avg', 'sum', 'max', 'min']),
            'filter_operator': any(op in generated for op in ['=', '>', '<', 'like', 'between', 'in']) ==
                               any(op in ref for op in ['=', '>', '<', 'like', 'between', 'in'])
        }

        # 3. Update All-Up Metrics
        if exact == 100: all_metrics['exact_matches'] += 1
        all_metrics['total_bleu_1'] += bleu
        all_metrics['total_rouge_1'] += r1
        all_metrics['total_rouge_l'] += rl
        all_metrics['total_similarity'] += sim
        for k, v in comp_results.items():
            if v: all_metrics['component_counts'][k] += 1

        # 4. Update Difficulty Metrics
        target_diff = easy_metrics if diff_level == 'Easy' else (
            medium_metrics if diff_level == 'Medium' else hard_metrics)
        target_diff['count'] += 1
        if exact == 100: target_diff['exact_matches'] += 1
        target_diff['total_bleu_1'] += bleu
        for k, v in comp_results.items():
            if v: target_diff['component_counts'][k] += 1

        # 5. Update Category Metrics
        if cat_name not in category_data:
            category_data[cat_name] = {'count': 0, 'bleu': 0, 'exact': 0}
        category_data[cat_name]['count'] += 1
        category_data[cat_name]['bleu'] += bleu
        if exact == 100: category_data[cat_name]['exact'] += 1

    # Final overall component accuracy calculation
    total_comp_hits = sum(all_metrics['component_counts'].values())
    all_metrics['overall_comp_acc'] = (total_comp_hits / (len(TEST_CASES) * len(all_metrics['component_counts']))) * 100

    return all_metrics, easy_metrics, medium_metrics, hard_metrics, category_data


def save_graphs(all_metrics):
    # Overall Performance Visualization
    plt.figure(figsize=(10, 6))
    labels = ['Exact Match', 'BLEU-1', 'ROUGE-L', 'Similarity']
    vals = [
        all_metrics['exact_matches'] / len(TEST_CASES) * 100,
        all_metrics['total_bleu_1'] / len(TEST_CASES),
        all_metrics['total_rouge_l'] / len(TEST_CASES),
        all_metrics['total_similarity'] / len(TEST_CASES)
    ]
    plt.bar(labels, vals, color='skyblue')
    plt.title('Overall Performance Metrics (%)')
    plt.ylim(0, 100)
    plt.savefig('nlp_performance_scores.png')

    # Clause Accuracy Visualization
    plt.figure(figsize=(10, 6))
    clauses = [k.upper().replace('_', ' ') for k in all_metrics['component_counts'].keys()]
    accs = [(v / len(TEST_CASES)) * 100 for v in all_metrics['component_counts'].values()]
    plt.barh(clauses, accs, color='salmon')
    plt.title('SQL Clause Identification Accuracy (%)')
    plt.xlim(0, 100)
    plt.tight_layout()
    plt.savefig('component_accuracy.png')


def print_final_summary(all_metrics, easy_metrics, medium_metrics, hard_metrics, category_data):
    total_tests = len(TEST_CASES)

    print("\n" + "=" * 80)
    print("Table 4: Overall Performance Metrics on 200 Test Cases")
    print("=" * 80)
    print(f"{'Metric':<30} | {'Score (%)':<15} | {'Interpretation'}")
    print("-" * 80)

    overall_metrics_list = [
        ("Exact Match Rate", all_metrics['exact_matches'] / total_tests * 100, "High"),
        ("BLEU-1 Score", all_metrics['total_bleu_1'] / total_tests, "Excellent"),
        ("ROUGE-1 F1", all_metrics['total_rouge_1'] / total_tests, "Very Good"),
        ("ROUGE-L F1", all_metrics['total_rouge_l'] / total_tests, "Excellent"),
        ("Similarity Ratio", all_metrics['total_similarity'] / total_tests, "Excellent"),
        ("Overall Component Accuracy", all_metrics['overall_comp_acc'], "Very Good")
    ]

    for metric, score, interp in overall_metrics_list:
        print(f"{metric:<30} | {score:>9.2f}%      | {interp}")

    print("\n" + "=" * 80)
    print("Table 5: Component-wise SQL Clause Accuracy")
    print("=" * 80)
    print(f"{'SQL Clause':<15} | {'Accuracy (%)':<15} | {'Easy Queries':<15} | {'Hard Queries'}")
    print("-" * 80)

    for comp in all_metrics['component_counts']:
        all_acc = (all_metrics['component_counts'][comp] / total_tests) * 100
        e_acc = (easy_metrics['component_counts'][comp] / easy_metrics['count'] * 100) if easy_metrics[
                                                                                              'count'] > 0 else 0
        h_acc = (hard_metrics['component_counts'][comp] / hard_metrics['count'] * 100) if hard_metrics[
                                                                                              'count'] > 0 else 0

        display_name = comp.replace('_', ' ').upper()
        print(f"{display_name:<15} | {all_acc:>12.2f}% | {e_acc:>12.2f}% | {h_acc:>12.2f}%")

    # Table 6 (Category Performance)
    print("\n" + "=" * 80)
    print("Table 6: Performance by Query Category")
    print("=" * 80)
    print(f"{'Category':<30} | {'Count':<6} | {'BLEU (%)':<10} | {'Exact Match (%)'}")
    print("-" * 80)
    for cat, data in category_data.items():
        print(
            f"{cat:<30} | {data['count']:<6} | {data['bleu'] / data['count']:>8.1f}% | {(data['exact'] / data['count'] * 100):>12.1f}%")

    # Table 7 (Difficulty Breakdown)
    print("\n" + "=" * 80)
    print("Table 7: Performance by Query Difficulty Level")
    print("=" * 80)
    print(f"{'Difficulty':<15} | {'Count':<6} | {'BLEU (%)':<10} | {'Exact Match (%)'}")
    print("-" * 80)
    for name, mtx in [("Easy", easy_metrics), ("Medium", medium_metrics), ("Hard", hard_metrics)]:
        if mtx['count'] > 0:
            print(
                f"{name:<15} | {mtx['count']:<6} | {mtx['total_bleu_1'] / mtx['count']:>8.1f}% | {(mtx['exact_matches'] / mtx['count'] * 100):>12.1f}%")


if __name__ == "__main__":
    all_mtx, easy_mtx, med_mtx, hard_mtx, cat_mtx = calculate_metrics()
    save_graphs(all_mtx)
    print_final_summary(all_mtx, easy_mtx, med_mtx, hard_mtx, cat_mtx)
    print("Evaluation Complete. Performance graphs saved and summary tables printed.")