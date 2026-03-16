"""Test cases for enhanced extractor."""
from extractor import extract_entities
from ir_builder import build_ir
from compiler import compile_mysql


# Test cases for expanded dictionaries
test_queries = [
    "Show me the top 10 students with highest CGPA",
    "What is the average marks of students?",
    "Find cars with price greater than 50000",
    "List students where CGPA is above 3.5",
    "Count the number of cars sold in 2024",
    "Show maximum price of cars",
    "Get minimum salary of employees",
    "Find products with rating between 4.0 and 5.0",
    "Show employees with salary less than 50000",
    "List the worst 5 performers by marks",
    "What is the mean CGPA of students?",
    "Show me vehicles costing below 30000",
    "Find the best 3 employees by rating",
    "Get total salary of all employees",
    "Show products with price above 100",
    "List students with marks at least 85",
    "Find cars with units sold more than 1000",
    "Show employees in department Engineering",
    "Get average rating of products",
    "Find the smallest quantity products"
]


def run_tests():
    """Run test queries through the full pipeline."""
    print("=" * 80)
    print("ENHANCED NLP-TO-SQL CONVERTER - TEST SUITE")
    print("=" * 80)

    passed = 0
    failed = 0

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}] Query: {query}")
        print("-" * 80)
        try:
            # Extract entities
            entities = extract_entities(query)
            print(f"Entities: {entities}")

            # Build IR
            ir = build_ir(entities)
            print(f"IR: {ir}")

            # Compile to SQL
            sql = compile_mysql(ir)
            print(f"SQL: {sql}")

            passed += 1
            print("Status: PASSED")

        except Exception as e:
            failed += 1
            print(f"Status: FAILED")
            print(f"Error: {e}")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_queries)} tests")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
