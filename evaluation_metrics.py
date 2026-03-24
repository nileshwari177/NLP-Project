"""
Evaluation Metrics for NLP to SQL System
Includes: BLEU, ROUGE, Exact Match, Semantic Similarity, Component-wise Accuracy
"""

import re
from typing import Dict, List, Tuple, Any
from collections import Counter
import difflib


class SQLNormalizer:
    """Normalize SQL queries for fair comparison"""

    @staticmethod
    def normalize(sql: str) -> str:
        """
        Normalize SQL query for comparison
        - Remove extra whitespace
        - Lowercase keywords
        - Standardize formatting
        """
        if not sql:
            return ""

        # Remove extra whitespace and newlines
        sql = ' '.join(sql.split())

        # Remove trailing semicolon for comparison
        sql = sql.rstrip(';').strip()

        # Normalize quotes (single vs double)
        # sql = sql.replace('"', "'")

        return sql

    @staticmethod
    def extract_components(sql: str) -> Dict[str, Any]:
        """
        Extract SQL components for component-wise evaluation

        Returns:
            Dict with SELECT, FROM, WHERE, ORDER BY, LIMIT clauses
        """
        sql_normalized = SQLNormalizer.normalize(sql).upper()

        components = {
            'select': None,
            'from': None,
            'where': None,
            'order_by': None,
            'limit': None,
            'aggregation': None
        }

        # Extract SELECT clause
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_normalized)
        if select_match:
            select_clause = select_match.group(1).strip()
            components['select'] = select_clause

            # Check for aggregation
            agg_match = re.search(r'(AVG|SUM|COUNT|MAX|MIN)\s*\(', select_clause)
            if agg_match:
                components['aggregation'] = agg_match.group(1)

        # Extract FROM clause
        from_match = re.search(r'FROM\s+(\w+)', sql_normalized)
        if from_match:
            components['from'] = from_match.group(1).strip()

        # Extract WHERE clause
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+LIMIT|\s*$)', sql_normalized)
        if where_match:
            components['where'] = where_match.group(1).strip()

        # Extract ORDER BY clause
        order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*$)', sql_normalized)
        if order_match:
            components['order_by'] = order_match.group(1).strip()

        # Extract LIMIT clause
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_normalized)
        if limit_match:
            components['limit'] = int(limit_match.group(1))

        return components


class BLEUScore:
    """Calculate BLEU score for SQL queries"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize SQL query into tokens"""
        # Split by whitespace and special characters
        tokens = re.findall(r'\w+|[^\w\s]', text.lower())
        return tokens

    @staticmethod
    def ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
        """Generate n-grams from tokens"""
        return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

    @staticmethod
    def calculate(reference: str, candidate: str, max_n: int = 4) -> Dict[str, float]:
        """
        Calculate BLEU score

        Args:
            reference: Ground truth SQL
            candidate: Generated SQL
            max_n: Maximum n-gram size (default 4)

        Returns:
            Dict with BLEU-1, BLEU-2, BLEU-3, BLEU-4, and overall BLEU
        """
        ref_tokens = BLEUScore.tokenize(reference)
        cand_tokens = BLEUScore.tokenize(candidate)

        if not cand_tokens:
            return {f'bleu_{i}': 0.0 for i in range(1, max_n + 1)} | {'bleu': 0.0}

        scores = {}
        precisions = []

        for n in range(1, max_n + 1):
            ref_ngrams = BLEUScore.ngrams(ref_tokens, n)
            cand_ngrams = BLEUScore.ngrams(cand_tokens, n)

            if not cand_ngrams:
                scores[f'bleu_{n}'] = 0.0
                continue

            # Count n-gram matches
            ref_counter = Counter(ref_ngrams)
            cand_counter = Counter(cand_ngrams)

            matches = sum((cand_counter & ref_counter).values())
            total = sum(cand_counter.values())

            precision = matches / total if total > 0 else 0.0
            precisions.append(precision)
            scores[f'bleu_{n}'] = precision

        # Calculate geometric mean for overall BLEU
        if precisions and all(p > 0 for p in precisions):
            import math
            bleu = math.exp(sum(math.log(p) for p in precisions) / len(precisions))
        else:
            bleu = 0.0

        scores['bleu'] = bleu

        return scores


class ROUGEScore:
    """Calculate ROUGE scores for SQL queries"""

    @staticmethod
    def calculate_rouge_n(reference: str, candidate: str, n: int = 1) -> Dict[str, float]:
        """
        Calculate ROUGE-N score

        Returns:
            Dict with precision, recall, f1
        """
        ref_tokens = BLEUScore.tokenize(reference)
        cand_tokens = BLEUScore.tokenize(candidate)

        ref_ngrams = BLEUScore.ngrams(ref_tokens, n)
        cand_ngrams = BLEUScore.ngrams(cand_tokens, n)

        if not ref_ngrams or not cand_ngrams:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

        ref_counter = Counter(ref_ngrams)
        cand_counter = Counter(cand_ngrams)

        matches = sum((ref_counter & cand_counter).values())

        precision = matches / sum(cand_counter.values()) if cand_counter else 0.0
        recall = matches / sum(ref_counter.values()) if ref_counter else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    @staticmethod
    def calculate_rouge_l(reference: str, candidate: str) -> Dict[str, float]:
        """
        Calculate ROUGE-L (Longest Common Subsequence) score

        Returns:
            Dict with precision, recall, f1
        """
        ref_tokens = BLEUScore.tokenize(reference)
        cand_tokens = BLEUScore.tokenize(candidate)

        # Calculate LCS length
        lcs_length = ROUGEScore._lcs_length(ref_tokens, cand_tokens)

        if not ref_tokens or not cand_tokens:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

        precision = lcs_length / len(cand_tokens)
        recall = lcs_length / len(ref_tokens)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    @staticmethod
    def _lcs_length(seq1: List[str], seq2: List[str]) -> int:
        """Calculate length of longest common subsequence"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])

        return dp[m][n]

    @staticmethod
    def calculate(reference: str, candidate: str) -> Dict[str, Any]:
        """
        Calculate all ROUGE scores

        Returns:
            Dict with ROUGE-1, ROUGE-2, ROUGE-L scores
        """
        rouge1 = ROUGEScore.calculate_rouge_n(reference, candidate, n=1)
        rouge2 = ROUGEScore.calculate_rouge_n(reference, candidate, n=2)
        rougel = ROUGEScore.calculate_rouge_l(reference, candidate)

        return {
            'rouge_1': rouge1,
            'rouge_2': rouge2,
            'rouge_l': rougel
        }


class ExactMatch:
    """Calculate exact match and similarity scores"""

    @staticmethod
    def calculate(reference: str, candidate: str) -> Dict[str, Any]:
        """
        Calculate exact match and similarity scores

        Returns:
            Dict with exact_match, normalized_match, edit_distance, similarity_ratio
        """
        # Exact match (case-insensitive, whitespace normalized)
        ref_normalized = SQLNormalizer.normalize(reference)
        cand_normalized = SQLNormalizer.normalize(candidate)

        exact_match = ref_normalized.lower() == cand_normalized.lower()

        # Edit distance (Levenshtein-like via difflib)
        similarity_ratio = difflib.SequenceMatcher(None, ref_normalized, cand_normalized).ratio()

        return {
            'exact_match': 1.0 if exact_match else 0.0,
            'similarity_ratio': similarity_ratio,
            'character_overlap': similarity_ratio  # Alias for clarity
        }


class ComponentAccuracy:
    """Calculate component-wise accuracy for SQL queries"""

    @staticmethod
    def calculate(reference: str, candidate: str) -> Dict[str, Any]:
        """
        Calculate accuracy for each SQL component

        Returns:
            Dict with accuracy for each component and overall score
        """
        ref_components = SQLNormalizer.extract_components(reference)
        cand_components = SQLNormalizer.extract_components(candidate)

        component_scores = {}
        total_components = 0
        correct_components = 0

        for key in ['select', 'from', 'where', 'order_by', 'limit', 'aggregation']:
            ref_val = ref_components.get(key)
            cand_val = cand_components.get(key)

            # Skip None values in reference
            if ref_val is None:
                component_scores[f'{key}_accuracy'] = None
                continue

            total_components += 1

            # Compare components
            if isinstance(ref_val, str) and isinstance(cand_val, str):
                match = ref_val.strip() == cand_val.strip()
            else:
                match = ref_val == cand_val

            component_scores[f'{key}_accuracy'] = 1.0 if match else 0.0

            if match:
                correct_components += 1

        # Overall component accuracy
        overall_accuracy = correct_components / total_components if total_components > 0 else 0.0
        component_scores['overall_component_accuracy'] = overall_accuracy

        return component_scores


class EvaluationMetrics:
    """Main evaluation metrics calculator"""

    @staticmethod
    def calculate_all(reference: str, candidate: str) -> Dict[str, Any]:
        """
        Calculate all evaluation metrics

        Args:
            reference: Ground truth SQL query
            candidate: Generated SQL query

        Returns:
            Dict with all metrics
        """
        metrics = {}

        # BLEU scores
        bleu_scores = BLEUScore.calculate(reference, candidate)
        metrics.update(bleu_scores)

        # ROUGE scores
        rouge_scores = ROUGEScore.calculate(reference, candidate)
        metrics.update({
            'rouge_1_f1': rouge_scores['rouge_1']['f1'],
            'rouge_1_precision': rouge_scores['rouge_1']['precision'],
            'rouge_1_recall': rouge_scores['rouge_1']['recall'],
            'rouge_2_f1': rouge_scores['rouge_2']['f1'],
            'rouge_2_precision': rouge_scores['rouge_2']['precision'],
            'rouge_2_recall': rouge_scores['rouge_2']['recall'],
            'rouge_l_f1': rouge_scores['rouge_l']['f1'],
            'rouge_l_precision': rouge_scores['rouge_l']['precision'],
            'rouge_l_recall': rouge_scores['rouge_l']['recall'],
        })

        # Exact match and similarity
        exact_match_scores = ExactMatch.calculate(reference, candidate)
        metrics.update(exact_match_scores)

        # Component accuracy
        component_scores = ComponentAccuracy.calculate(reference, candidate)
        metrics.update(component_scores)

        return metrics

    @staticmethod
    def aggregate_results(all_metrics: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Aggregate metrics across multiple test cases

        Args:
            all_metrics: List of metric dictionaries

        Returns:
            Dict with aggregated metrics (mean values)
        """
        if not all_metrics:
            return {}

        aggregated = {}
        metric_keys = all_metrics[0].keys()

        for key in metric_keys:
            # Skip None values
            values = [m[key] for m in all_metrics if m[key] is not None]
            if values:
                aggregated[f'avg_{key}'] = sum(values) / len(values)
            else:
                aggregated[f'avg_{key}'] = None

        return aggregated

    @staticmethod
    def print_metrics(metrics: Dict[str, Any], title: str = "Evaluation Metrics"):
        """Pretty print metrics"""
        print(f"\n{'='*70}")
        print(f"{title:^70}")
        print(f"{'='*70}\n")

        # Group metrics by category
        bleu_metrics = {k: v for k, v in metrics.items() if 'bleu' in k}
        rouge_metrics = {k: v for k, v in metrics.items() if 'rouge' in k}
        exact_metrics = {k: v for k, v in metrics.items() if 'exact' in k or 'similarity' in k or 'overlap' in k}
        component_metrics = {k: v for k, v in metrics.items() if 'accuracy' in k}

        if bleu_metrics:
            print("BLEU Scores:")
            for key, value in bleu_metrics.items():
                if value is not None:
                    print(f"  {key:25s}: {value:6.4f} ({value*100:5.2f}%)")
            print()

        if rouge_metrics:
            print("ROUGE Scores:")
            for key, value in rouge_metrics.items():
                if value is not None:
                    print(f"  {key:25s}: {value:6.4f} ({value*100:5.2f}%)")
            print()

        if exact_metrics:
            print("Exact Match & Similarity:")
            for key, value in exact_metrics.items():
                if value is not None:
                    print(f"  {key:25s}: {value:6.4f} ({value*100:5.2f}%)")
            print()

        if component_metrics:
            print("Component-wise Accuracy:")
            for key, value in component_metrics.items():
                if value is not None:
                    print(f"  {key:25s}: {value:6.4f} ({value*100:5.2f}%)")
            print()

        print(f"{'='*70}\n")


# Example usage
if __name__ == "__main__":
    # Test the metrics
    reference_sql = "SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;"
    candidate_sql = "SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;"

    print("Testing Evaluation Metrics\n")
    print(f"Reference: {reference_sql}")
    print(f"Candidate: {candidate_sql}\n")

    metrics = EvaluationMetrics.calculate_all(reference_sql, candidate_sql)
    EvaluationMetrics.print_metrics(metrics, "Perfect Match Test")

    # Test with imperfect match
    candidate_sql_2 = "SELECT id, marks FROM students ORDER BY marks DESC LIMIT 10;"
    print(f"\nReference: {reference_sql}")
    print(f"Candidate: {candidate_sql_2}\n")

    metrics_2 = EvaluationMetrics.calculate_all(reference_sql, candidate_sql_2)
    EvaluationMetrics.print_metrics(metrics_2, "Imperfect Match Test")
