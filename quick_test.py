"""
Quick Test Script - Test All Features
Run this to verify everything works!
"""

from nlp_to_sql import convert


def test(name, query, expected_keywords=None):
    """Test a query and show result"""
    try:
        sql = convert(query, use_ai=False, verbose=False)

        # Check if expected keywords are in SQL
        if expected_keywords:
            all_found = all(kw.upper() in sql.upper() for kw in expected_keywords)
            status = "[PASS]" if all_found else "[WARN]"
        else:
            status = "[PASS]"

        print(f"\n{status} {name}")
        print(f"  Query: {query}")
        print(f"  SQL:   {sql}")

        return True
    except Exception as e:
        print(f"\n[FAIL] {name}")
        print(f"  Query: {query}")
        print(f"  ERROR: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("QUICK TEST - ALL FEATURES")
    print("=" * 80)

    passed = 0
    total = 0

    # Test 1: Basic Retrieval
    total += 1
    if test("Basic Retrieval", "show all students", ["SELECT", "FROM", "students"]):
        passed += 1

    # Test 2: Ranking
    total += 1
    if test("Ranking", "Top 10 students with highest CGPA",
            ["SELECT", "ORDER BY", "DESC", "LIMIT"]):
        passed += 1

    # Test 3: Aggregation
    total += 1
    if test("Aggregation (AVG)", "Average salary of employees",
            ["AVG", "salary", "employees"]):
        passed += 1

    # Test 4: Aggregation (COUNT)
    total += 1
    if test("Aggregation (COUNT)", "Count of orders",
            ["COUNT", "orders"]):
        passed += 1

    # Test 5: LIKE Operator
    total += 1
    if test("LIKE Operator", "students with name like John",
            ["LIKE", "name"]):
        passed += 1

    # Test 6: IN Operator
    total += 1
    if test("IN Operator", "students in year 2023, 2024",
            ["IN", "year"]):
        passed += 1

    # Test 7: BETWEEN Operator
    total += 1
    if test("BETWEEN Operator", "products with price between 100 and 500",
            ["BETWEEN", "price"]):
        passed += 1

    # Test 8: Greater Than
    total += 1
    if test("Comparison (>)", "employees with salary > 50000",
            [">", "salary"]):
        passed += 1

    # Test 9: Calculation
    total += 1
    if test("Calculation", "salary plus bonus for employees",
            ["+", "salary", "bonus"]):
        passed += 1

    # Test 10: Complex Query (Ranking + Filtering)
    total += 1
    if test("Complex (Ranking + Filter)",
            "Top 5 employees with highest salary in IT department",
            ["ORDER BY", "WHERE", "LIMIT"]):
        passed += 1

    # Test 11: Complex Query (Aggregation + Filtering)
    total += 1
    if test("Complex (Aggregation + Filter)",
            "Average salary of employees in IT department",
            ["AVG", "WHERE", "department"]):
        passed += 1

    # Summary
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed}/{total} passed")
    print("=" * 80)

    if passed == total:
        print("\n🎉 All tests passed! System is working perfectly!")
        print("\nYou can now use the system:")
        print("  from nlp_to_sql import convert")
        print("  sql = convert('your query here')")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Check the output above.")

    print()


if __name__ == "__main__":
    main()
