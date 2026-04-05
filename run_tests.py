"""
Simple Test Runner
Tests both confident queries and ambiguous queries that trigger AI
"""

from nlp_to_sql import convert


def main():
    print("=" * 80)
    print("NLP-TO-SQL TEST RUNNER")
    print("=" * 80)

    # CONFIDENT QUERIES (High confidence, no AI needed)
    print("\n>>> CONFIDENT QUERIES (RapidFuzz + Multi-Strategy Extraction)")
    print("-" * 80)

    confident_queries = [
        "Top 10 students with highest CGPA",
        "Average salary of employees in IT department",
        "students with name like John",
    ]

    for query in confident_queries:
        print(f"\nQuery: {query}")
        sql = convert(query, use_ai=False, verbose=False)
        print(f"SQL:   {sql}")

    # AMBIGUOUS QUERIES (Low confidence, triggers AI)
    print("\n\n>>> AMBIGUOUS QUERIES (Triggers AI Disambiguator)")
    print("-" * 80)

    ambiguous_queries = [
        "show high performing students",  # Ambiguous: what is "high performing"?
        "employees with good salary",     # Ambiguous: what is "good"?
    ]

    for query in ambiguous_queries:
        print(f"\nQuery: {query}")
        try:
            sql = convert(query, use_ai=True, verbose=True)
            print(f"\nFinal SQL: {sql}")
        except Exception as e:
            print(f"Note: AI requires API key. Error: {e}")
            print("Falling back to non-AI mode...")
            sql = convert(query, use_ai=False, verbose=False)
            print(f"SQL: {sql}")

    print("\n" + "=" * 80)
    print("TESTS COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
