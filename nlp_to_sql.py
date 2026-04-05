"""
Modular NLP-to-SQL with Advanced Features
Combines clean modular architecture with powerful extraction:
- RapidFuzz fuzzy matching
- AI Disambiguator
- NLTK preprocessing
- Multi-strategy extraction

Pipeline: query → preprocess → extract (fuzzy+AI) → build → sql
"""

from extractor import extract
from builder import build


def convert(query: str, verbose: bool = False, use_ai: bool = True) -> str:
    """
    Convert natural language to SQL using advanced modular pipeline

    Args:
        query: Natural language query
        verbose: Show extraction details
        use_ai: Enable AI disambiguator for unclear queries

    Returns:
        SQL query string
    """
    # Step 1: Extract keywords (with fuzzy matching, AI, preprocessing)
    data = extract(query, use_ai=use_ai, use_preprocessing=True)

    # Step 2: Build SQL (with advanced query processor)
    sql = build(data)

    # Optional: Show extraction details
    if verbose:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        print(f"Preprocessed: {data.get('preprocessed_query', query)}")
        print(f"Table: {data.get('table', 'N/A')}")
        print(f"Primary Column: {data.get('primary_column', 'N/A')}")
        print(f"Intent: {data.get('intent', 'N/A')}")

        if data.get('aggregation'):
            print(f"Aggregation: {data['aggregation']}")

        if data.get('filters'):
            print(f"Filters: {len(data['filters'])} condition(s)")
            for f in data['filters']:
                print(f"  - {f['column']} {f['operator']} {f['value']}")

        if data.get('has_calculation'):
            print(f"Calculation: {data.get('calculation')}")

        if data.get('ranking_direction'):
            print(f"Ranking: {data['ranking_direction']} LIMIT {data.get('limit')}")

        if data.get('ai_disambiguation_used'):
            print(f"AI Disambiguator: USED ✓")

        print(f"\n{'='*80}")
        print(f"Generated SQL:")
        print(f"{'='*80}")
        print(f"{sql}")
        print(f"{'='*80}\n")

    return sql


def main():
    """Demo - test all features with advanced extraction"""
    print("=" * 80)
    print("MODULAR NLP-TO-SQL WITH ADVANCED FEATURES")
    print("RapidFuzz | AI Disambiguator | NLTK | Multi-Strategy Extraction")
    print("=" * 80)

    tests = [
        # Basic queries
        "Top 10 students with highest CGPA",
        "Average salary of employees in IT department",
        "Count of orders",

        # Filtering with advanced operators
        "students with name like John",
        "students in year 2023, 2024",
        "products with price between 100 and 500",
        "employees with salary greater than 50000",

        # Calculations
        "salary plus bonus for employees",

        # Fuzzy matching test
        "studnts with high cgpa",  # Typo - RapidFuzz should handle
        "avarage salery of employes",  # Multiple typos

        # Complex queries
        "Top 5 employees with highest salary in IT department",
    ]

    for query in tests:
        try:
            sql = convert(query, verbose=False, use_ai=True)
            print(f"\n{query}")
            print(f"  SQL: {sql}")
        except Exception as e:
            print(f"\n{query}")
            print(f"  ERROR: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
