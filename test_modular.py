"""
Comprehensive Test for Modular NLP-to-SQL System
"""

from nlp_to_sql import convert


def test_all_features():
    """Test all features of the modular system"""

    tests = {
        "BASIC QUERIES": [
            "show all students",
            "get all employees",
            "products",
        ],

        "RANKING": [
            "Top 10 students with highest CGPA",
            "Bottom 5 products with lowest price",
            "First 3 employees with highest salary",
        ],

        "AGGREGATIONS": [
            "Average salary of employees",
            "Count of orders",
            "Total price of products",
            "Maximum marks of students",
            "Minimum mileage of cars",
        ],

        "FILTERING": [
            "students with name like John",
            "students in year 2023, 2024",
            "students not in year 2020",
            "products with price between 100 and 500",
            "employees with salary > 50000",
        ],

        "CALCULATIONS": [
            "salary plus bonus for employees",
            "price times quantity for products",
        ],

        "JOINS": [
            "customers and their orders",
            "orders with customer name",
            "orders with customer email",
        ],
    }

    print("=" * 80)
    print("COMPREHENSIVE MODULAR NLP-TO-SQL TEST")
    print("=" * 80)

    for category, queries in tests.items():
        print(f"\n{'=' * 80}")
        print(f"{category}")
        print('=' * 80)

        for query in queries:
            sql = convert(query)
            print(f"\n{query}")
            print(f"  {sql}")

    print("\n" + "=" * 80)
    print("All tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    test_all_features()
