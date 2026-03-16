from interactive_nlp_extractor import NLPExtractor
from interactive_query_processor import QueryProcessor
from ai_disambiguator import AmbiguityDetector


def test_query(extractor, processor, query):
    """Test a single query"""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('='*70)

    # Extract keywords
    keywords = extractor.extract_keywords(query)

    # Show extracted info
    print(f"\nExtracted Information:")
    print(f"  Table: {keywords['table']} ({keywords['table_confidence']:.1f}%)")
    print(f"  Column: {keywords['primary_column']} ({keywords['column_confidence']:.1f}%)")
    print(f"  Aggregation: {keywords['aggregation']}")
    print(f"  Ranking: {keywords['ranking_direction']} (limit: {keywords['limit']})")
    print(f"  Filters: {len(keywords['filters'])} condition(s)")
    print(f"  Intent: {keywords['intent']}")

    # Check ambiguities
    is_ambiguous, issues, suggestions = AmbiguityDetector.detect(keywords)
    print(f"\nAmbiguity Check:")
    print(f"  Ambiguous: {is_ambiguous}")
    if is_ambiguous:
        print(f"  Issues: {', '.join(issues)}")
        print(f"  Suggestions: {suggestions}")

    # Generate SQL
    try:
        sql = processor.process(keywords)
        explanation = processor.explain_query(keywords, sql)

        print(f"\nGenerated SQL:")
        print(f"  {sql}")
        print(f"\nExplanation:")
        print(f"  {explanation}")

        return True
    except Exception as e:
        print(f"\nError: {e}")
        return False


def main():
    """Run tests"""
    print("TESTING INTERACTIVE NLP SYSTEM")
    print("="*70)

    extractor = NLPExtractor()
    processor = QueryProcessor()

    test_queries = [
        # Basic retrieval
        "Show all students",

        # Aggregation
        "What is the average marks of students?",
        "Calculate total salary of employees",

        # Ranking
        "Show top 10 students with highest CGPA",
        "Get bottom 5 cars with lowest price",

        # Filtering
        "Find students with marks greater than 80",
        "Show cars with price between 20000 and 50000",
        "Get employees in department Engineering",

        # Complex
        "Top 5 employees with highest salary in IT department",
        "Average rating of products in category Electronics",
    ]

    passed = 0
    failed = 0

    for query in test_queries:
        if test_query(extractor, processor, query):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*70}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print('='*70)


if __name__ == "__main__":
    main()
