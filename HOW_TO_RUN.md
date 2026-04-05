# How to Run and Test the NLP-to-SQL System

## Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install rapidfuzz nltk anthropic
```

### 2. Run the Demo
```bash
python nlp_to_sql.py
```

### 3. Test Everything
```bash
python test_modular.py
```

---

## Installation (Detailed)

### Step 1: Check Python Version
```bash
python --version
# Should be Python 3.8 or higher
```

### Step 2: Install Required Packages
```bash
pip install rapidfuzz nltk anthropic
```

**What each package does:**
- `rapidfuzz` - Fuzzy string matching for typo tolerance
- `nltk` - Natural Language Toolkit for preprocessing
- `anthropic` - Claude AI API (optional, for disambiguation)

### Step 3: Download NLTK Data (First Time Only)
```bash
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

This downloads:
- WordNet dictionary for lemmatization
- Open Multilingual WordNet for better synonym support

---

## Running the System

### Method 1: Demo Mode (Recommended for First Time)
```bash
python nlp_to_sql.py
```

**What you'll see:**
```
================================================================================
MODULAR NLP-TO-SQL WITH ADVANCED FEATURES
RapidFuzz | AI Disambiguator | NLTK | Multi-Strategy Extraction
================================================================================

Top 10 students with highest CGPA
  SQL: SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;

Average salary of employees in IT department
  SQL: SELECT AVG(salary) as result FROM employees WHERE department = 'it';

students with name like John
  SQL: SELECT * FROM students WHERE name LIKE '%john%';

... and more examples
```

### Method 2: Python Script
```python
# test_my_query.py
from nlp_to_sql import convert

# Simple query
sql = convert("Top 10 students with highest CGPA")
print(sql)
# Output: SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;

# With verbose mode (shows extraction details)
sql = convert("Average salary of employees", verbose=True)
```

**Run it:**
```bash
python test_my_query.py
```

### Method 3: Interactive Python
```bash
python
```

```python
>>> from nlp_to_sql import convert

>>> sql = convert("show all students")
>>> print(sql)
SELECT * FROM students;

>>> sql = convert("students with cgpa > 3.5")
>>> print(sql)
SELECT * FROM students WHERE cgpa > 3.5;

>>> exit()
```

### Method 4: Command Line (One Query)
```python
# quick_test.py
import sys
from nlp_to_sql import convert

query = sys.argv[1] if len(sys.argv) > 1 else "show all students"
sql = convert(query, verbose=True)
print(f"\nGenerated SQL:\n{sql}")
```

**Run it:**
```bash
python quick_test.py "Top 10 students with highest CGPA"
```

---

## Testing the System

### Test 1: Run Comprehensive Tests
```bash
python test_modular.py
```

**What it tests:**
- Basic queries (SELECT *)
- Ranking queries (TOP N)
- Aggregations (COUNT, AVG, SUM, MAX, MIN)
- Filtering (WHERE conditions)
- LIKE operator
- IN operator
- BETWEEN operator
- Calculations (salary + bonus)

**Expected output:**
```
================================================================================
COMPREHENSIVE MODULAR NLP-TO-SQL TEST
================================================================================

[BASIC QUERIES]
show all students
  SELECT * FROM students;

[RANKING]
Top 10 students with highest CGPA
  SELECT students.id, students.cgpa FROM students ORDER BY cgpa DESC LIMIT 10;

... and more tests
```

### Test 2: Test Specific Features

**Create a test file:**
```python
# my_tests.py
from nlp_to_sql import convert

def test_feature(name, query):
    print(f"\n{name}:")
    print(f"  Query: {query}")
    sql = convert(query)
    print(f"  SQL: {sql}")

# Test various features
test_feature("Basic Retrieval", "show all students")
test_feature("Ranking", "Top 10 students with highest CGPA")
test_feature("Aggregation", "Average salary of employees")
test_feature("LIKE", "students with name like John")
test_feature("IN", "students in year 2023, 2024")
test_feature("BETWEEN", "products with price between 100 and 500")
test_feature("Calculation", "salary plus bonus for employees")
test_feature("Complex", "Top 5 employees with highest salary in IT department")
```

**Run it:**
```bash
python my_tests.py
```

### Test 3: Test with Verbose Mode
```python
# verbose_test.py
from nlp_to_sql import convert

query = "Top 5 employees with highest salary in IT department"

print("Testing with verbose mode:")
print("=" * 80)

sql = convert(query, verbose=True, use_ai=False)

print("\nFinal SQL:", sql)
```

**Run it:**
```bash
python verbose_test.py
```

**Expected output:**
```
================================================================================
Query: Top 5 employees with highest salary in IT department
================================================================================
Preprocessed: top 5 employee with highest salary in it department
Table: employees
Primary Column: salary
Intent: ranking
Filters: 1 condition(s)
  - department = it
Ranking: DESC LIMIT 5

================================================================================
Generated SQL:
================================================================================
SELECT id, salary FROM employees WHERE department = 'it' ORDER BY salary DESC LIMIT 5;
================================================================================
```

---

## Example Test Queries

### Basic Queries
```python
from nlp_to_sql import convert

# 1. Simple retrieval
convert("show all students")
# SELECT * FROM students;

# 2. Show specific table
convert("get all employees")
# SELECT * FROM employees;
```

### Filtering Queries
```python
# 3. Greater than
convert("students with cgpa > 3.5")
# SELECT * FROM students WHERE cgpa > 3.5;

# 4. Equals
convert("employees in IT department")
# SELECT * FROM employees WHERE department = 'IT';

# 5. LIKE operator
convert("students with name like John")
# SELECT * FROM students WHERE name LIKE '%john%';

# 6. IN operator
convert("students in year 2023, 2024")
# SELECT * FROM students WHERE year IN (2023, 2024);

# 7. NOT IN operator
convert("students not in year 2020")
# SELECT * FROM students WHERE year NOT IN (2020);

# 8. BETWEEN operator
convert("products with price between 100 and 500")
# SELECT * FROM products WHERE price BETWEEN 100 AND 500;
```

### Ranking Queries
```python
# 9. Top N
convert("Top 10 students with highest CGPA")
# SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;

# 10. Bottom N
convert("Bottom 5 products with lowest price")
# SELECT id, price FROM products ORDER BY price ASC LIMIT 5;

# 11. First N
convert("First 3 employees with highest salary")
# SELECT id, salary FROM employees ORDER BY salary DESC LIMIT 3;
```

### Aggregation Queries
```python
# 12. Average
convert("Average salary of employees")
# SELECT AVG(salary) as result FROM employees;

# 13. Count
convert("Count of orders")
# SELECT COUNT(id) as result FROM orders;

# 14. Sum
convert("Total price of products")
# SELECT SUM(price) as result FROM products;

# 15. Maximum
convert("Maximum marks of students")
# SELECT MAX(marks) as result FROM students;

# 16. Minimum
convert("Minimum mileage of cars")
# SELECT MIN(mileage) as result FROM cars;
```

### Calculation Queries
```python
# 17. Addition
convert("salary plus bonus for employees")
# SELECT salary + bonus as result FROM employees;

# 18. Multiplication
convert("price times quantity for products")
# SELECT price * quantity as result FROM products;
```

### Complex Queries
```python
# 19. Ranking + Filtering
convert("Top 5 employees with highest salary in IT department")
# SELECT id, salary FROM employees WHERE department = 'it' ORDER BY salary DESC LIMIT 5;

# 20. Aggregation + Filtering
convert("Average salary of employees in IT department")
# SELECT AVG(salary) as result FROM employees WHERE department = 'it';
```

---

## Testing with AI Disambiguator (Optional)

### Setup Claude API (Optional)
If you want to test the AI disambiguator feature:

1. Get API key from https://console.anthropic.com/
2. Set environment variable:
```bash
# On Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key-here"

# On Windows (CMD)
set ANTHROPIC_API_KEY=your-api-key-here

# On Linux/Mac
export ANTHROPIC_API_KEY=your-api-key-here
```

3. Test with AI enabled:
```python
from nlp_to_sql import convert

# Enable AI for ambiguous queries
sql = convert("students with high marks", use_ai=True, verbose=True)
```

**Note:** AI is optional. The system works perfectly without it using RapidFuzz fuzzy matching!

---

## Troubleshooting

### Issue 1: ModuleNotFoundError
```
ModuleNotFoundError: No module named 'rapidfuzz'
```

**Fix:**
```bash
pip install rapidfuzz nltk anthropic
```

### Issue 2: NLTK Data Not Found
```
LookupError: Resource wordnet not found
```

**Fix:**
```bash
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### Issue 3: Import Errors
```
ModuleNotFoundError: No module named 'interactive_nlp_extractor'
```

**Fix:** Make sure you're in the correct directory:
```bash
cd C:\Users\Mrudul\desktop\project\NLP-Project
python nlp_to_sql.py
```

### Issue 4: No Output
If you run a script and see no output, add print statements:
```python
from nlp_to_sql import convert

query = "show all students"
print(f"Testing query: {query}")

sql = convert(query)
print(f"Generated SQL: {sql}")
```

---

## Quick Test Script

Create this file to test everything quickly:

```python
# quick_test_all.py
from nlp_to_sql import convert

def test(name, query):
    try:
        sql = convert(query, use_ai=False)
        print(f"✓ {name}")
        print(f"  {sql}\n")
    except Exception as e:
        print(f"✗ {name}")
        print(f"  ERROR: {e}\n")

print("="*80)
print("QUICK TEST - ALL FEATURES")
print("="*80 + "\n")

# Test each feature
test("Basic Retrieval", "show all students")
test("Ranking", "Top 10 students with highest CGPA")
test("Aggregation", "Average salary of employees")
test("LIKE Operator", "students with name like John")
test("IN Operator", "students in year 2023, 2024")
test("BETWEEN Operator", "products with price between 100 and 500")
test("Calculation", "salary plus bonus for employees")
test("Complex Query", "Top 5 employees with highest salary in IT department")

print("="*80)
print("TEST COMPLETE!")
print("="*80)
```

**Run it:**
```bash
python quick_test_all.py
```

---

## Performance Testing

Want to test speed? Create this:

```python
# performance_test.py
import time
from nlp_to_sql import convert

queries = [
    "show all students",
    "Top 10 students with highest CGPA",
    "Average salary of employees",
    "students with name like John",
    "students in year 2023, 2024",
]

print("Performance Test\n" + "="*80)

total_time = 0
for i, query in enumerate(queries, 1):
    start = time.time()
    sql = convert(query, use_ai=False)
    elapsed = time.time() - start
    total_time += elapsed

    print(f"\n{i}. {query}")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   SQL: {sql}")

print(f"\n{'='*80}")
print(f"Total time: {total_time:.3f}s")
print(f"Average time per query: {total_time/len(queries):.3f}s")
```

**Run it:**
```bash
python performance_test.py
```

---

## Summary

**To get started (3 commands):**
```bash
pip install rapidfuzz nltk anthropic
python nlp_to_sql.py
python test_modular.py
```

**To test your own queries:**
```python
from nlp_to_sql import convert
sql = convert("your query here")
print(sql)
```

**That's it!** 🚀

The system is ready to use. All advanced features (RapidFuzz, NLTK, multi-strategy extraction) work automatically behind the clean modular interface.
