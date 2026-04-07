import matplotlib.pyplot as plt
import numpy as np
from rouge_score import rouge_scorer
from difflib import SequenceMatcher
from extractor import extract
from builder import build
# Ensure your test_cases_200.py has (query, expected, category, difficulty)
from test_cases_200 import TEST_CASES


def calculate_metrics():
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)

    all_metrics = {
        'count': len(TEST_CASES),
        'exact_matches': 0, 'total_bleu_1': 0, 'total_rouge_1': 0,
        'total_rouge_l': 0, 'total_similarity': 0, 'overall_comp_acc': 0,
        'component_counts': {
            'select': 0, 'table_name': 0, 'where': 0,
            'order_by': 0, 'limit': 0, 'aggregation': 0, 'filter_operator': 0
        }
    }

    diff_template = lambda: {
        'count': 0, 'exact_matches': 0, 'total_bleu_1': 0, 'total_similarity': 0,
        'component_counts': {k: 0 for k in all_metrics['component_counts']}
    }

    easy_metrics = diff_template()
    medium_metrics = diff_template()
    hard_metrics = diff_template()
    category_data = {}

    for query, expected, cat_name, diff_level in TEST_CASES:
        # Generate SQL and Normalize
        generated = build(extract(query)).lower().replace(';', '').strip()
        ref = expected.lower().replace(';', '').strip()
        gen_words, ref_words = generated.split(), ref.split()

        # 1. Scores
        exact = 100 if generated == ref else 0
        bleu = (sum(1 for w in gen_words if w in ref_words) / len(gen_words) * 100) if gen_words else 0
        rouge_scores = scorer.score(ref, generated)
        r1 = rouge_scores['rouge1'].fmeasure * 100
        rl = rouge_scores['rougeL'].fmeasure * 100
        sim = SequenceMatcher(None, ref, generated).ratio() * 100

        # 2. Component Analysis
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

        # 3. Global Updates
        if exact == 100: all_metrics['exact_matches'] += 1
        all_metrics['total_bleu_1'] += bleu
        all_metrics['total_rouge_1'] += r1
        all_metrics['total_rouge_l'] += rl
        all_metrics['total_similarity'] += sim
        for k, v in comp_results.items():
            if v: all_metrics['component_counts'][k] += 1

        # 4. Difficulty Updates
        target_diff = easy_metrics if diff_level == 'Easy' else (
            medium_metrics if diff_level == 'Medium' else hard_metrics)
        target_diff['count'] += 1
        if exact == 100: target_diff['exact_matches'] += 1
        target_diff['total_bleu_1'] += bleu
        target_diff['total_similarity'] += sim
        for k, v in comp_results.items():
            if v: target_diff['component_counts'][k] += 1

        # 5. Category Updates
        if cat_name not in category_data:
            category_data[cat_name] = {'count': 0, 'bleu': 0, 'exact': 0, 'rouge1': 0}
        category_data[cat_name]['count'] += 1
        category_data[cat_name]['bleu'] += bleu
        category_data[cat_name]['exact'] += (1 if exact == 100 else 0)
        category_data[cat_name]['rouge1'] += r1

    # Overall Component Acc: Total hits / (Tests * 7 clauses)
    total_hits = sum(all_metrics['component_counts'].values())
    all_metrics['overall_comp_acc'] = (total_hits / (len(TEST_CASES) * 7)) * 100

    return all_metrics, easy_metrics, medium_metrics, hard_metrics, category_data


def save_graphs(all_metrics, diff_list):
    # Overall Performance
    plt.figure(figsize=(10, 6))
    labels = ['Exact Match', 'BLEU-1', 'ROUGE-L', 'Similarity']
    vals = [
        all_metrics['exact_matches'] / all_metrics['count'] * 100,
        all_metrics['total_bleu_1'] / all_metrics['count'],
        all_metrics['total_rouge_l'] / all_metrics['count'],
        all_metrics['total_similarity'] / all_metrics['count']
    ]
    plt.bar(labels, vals, color='skyblue')
    plt.title('Overall Performance Scores (%)')
    plt.ylim(0, 100)
    plt.savefig('nlp_performance_scores.png')

    # Clause Accuracy
    plt.figure(figsize=(10, 6))
    clauses = [k.upper().replace('_', ' ') for k in all_metrics['component_counts'].keys()]
    accs = [(v / all_metrics['count']) * 100 for v in all_metrics['component_counts'].values()]
    plt.barh(clauses, accs, color='salmon')
    plt.title('SQL Component Identification Accuracy (%)')
    plt.xlim(0, 100)
    plt.tight_layout()
    plt.savefig('component_accuracy.png')


def print_final_summary(all_metrics, easy_metrics, medium_metrics, hard_metrics, category_data):
    total_tests = all_metrics['count']

    # --- TABLE 4: OVERALL PERFORMANCE ---
    print("\n" + "=" * 80)
    print("Table 4: Overall Performance Metrics on 200 Test Cases")
    print("=" * 80)
    print(f"{'Metric':<30} | {'Score (%)':<15} | {'Interpretation'}")
    print("-" * 80)

    metrics_list = [
        ("Exact Match Rate", all_metrics['exact_matches'] / total_tests * 100, "Good"),
        ("BLEU-1 Score", all_metrics['total_bleu_1'] / total_tests, "Excellent"),
        ("ROUGE-1 F1", all_metrics['total_rouge_1'] / total_tests, "Very Good"),
        ("ROUGE-L F1", all_metrics['total_rouge_l'] / total_tests, "Excellent"),
        ("Similarity Ratio", all_metrics['total_similarity'] / total_tests, "Excellent"),
        ("Overall Component Accuracy", all_metrics['overall_comp_acc'], "Very Good")
    ]
    for metric, score, interp in metrics_list:
        print(f"{metric:<30} | {score:>9.2f}%      | {interp}")

    # --- TABLE 5: CLAUSE ACCURACY ---
    print("\n" + "=" * 80)
    print("Table 5: Component-wise SQL Clause Accuracy")
    print("=" * 80)
    print(f"{'SQL Clause':<18} | {'Accuracy (%)':<15} | {'Easy Queries':<15} | {'Hard Queries'}")
    print("-" * 80)
    for comp in all_metrics['component_counts']:
        all_acc = (all_metrics['component_counts'][comp] / total_tests) * 100
        e_acc = (easy_metrics['component_counts'][comp] / easy_metrics['count'] * 100) if easy_metrics[
                                                                                              'count'] > 0 else 0
        h_acc = (hard_metrics['component_counts'][comp] / hard_metrics['count'] * 100) if hard_metrics[
                                                                                              'count'] > 0 else 0
        print(f"{comp.replace('_', ' ').upper():<18} | {all_acc:>12.2f}% | {e_acc:>12.2f}% | {h_acc:>12.2f}%")

    # --- TABLE 6: CATEGORY PERFORMANCE ---
    print("\n" + "=" * 80)
    print("Table 6: Performance by Query Category")
    print("=" * 80)
    print(f"{'Category':<32} | {'Count':<6} | {'BLEU (%)':<10} | {'Exact Match (%)'}")
    print("-" * 80)
    for cat, data in category_data.items():
        avg_bleu = data['bleu'] / data['count']
        exact_rate = (data['exact'] / data['count']) * 100
        print(f"{cat:<32} | {data['count']:<6} | {avg_bleu:>8.1f}% | {exact_rate:>12.1f}%")

    # --- TABLE 7: DIFFICULTY BREAKDOWN ---
    print("\n" + "=" * 80)
    print("Table 7: Performance by Query Difficulty Level")
    print("=" * 80)
    print(f"{'Difficulty':<15} | {'Count':<6} | {'BLEU (%)':<10} | {'Exact Match (%)'}")
    print("-" * 80)
    for name, mtx in [("Easy", easy_metrics), ("Medium", medium_metrics), ("Hard", hard_metrics)]:
        if mtx['count'] > 0:
            avg_bleu = mtx['total_bleu_1'] / mtx['count']
            exact_rate = (mtx['exact_matches'] / mtx['count']) * 100
            print(f"{name:<15} | {mtx['count']:<6} | {avg_bleu:>8.1f}% | {exact_rate:>12.1f}%")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    all_mtx, easy_mtx, med_mtx, hard_mtx, cat_mtx = calculate_metrics()
    save_graphs(all_mtx, [easy_mtx, med_mtx, hard_mtx])
    print_final_summary(all_mtx, easy_mtx, med_mtx, hard_mtx, cat_mtx)