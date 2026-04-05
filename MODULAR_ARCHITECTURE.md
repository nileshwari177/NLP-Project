# Modular NLP-to-SQL Architecture

## Overview
This is a highly modular, pipeline-style NLP-to-SQL system where each function does ONE thing and data flows cleanly from one step to the next.

## Core Principle
**Pass one thing to another** - Each function takes input, does one task, returns output that feeds into the next function.

## Architecture

### 3 Core Files

1. **simple_extractor.py** - Extract keywords using modular functions
2. **simple_builder.py** - Build SQL using modular functions
3. **nlp_to_sql.py** - Main pipeline that connects everything

## The Pipeline

```
Natural Language Query
        ↓
    extract()
        ↓
    [Dictionary with extracted data]
        ↓
    build()
        ↓
    SQL Query
```

## Extraction Pipeline (simple_extractor.py)

Each function extracts ONE piece of information:

```python
query → extract_tables()      → ['students', 'courses']
     → extract_columns()     → {'students': ['name', 'cgpa']}
     → extract_intent()      → 'ranking'
     → extract_aggregation() → 'AVG'
     → extract_filters()     → [{'column': 'year', 'operator': '>', 'value': 2020}]
     → extract_calculation() → 'salary + bonus'
     → extract_join()        → {'type': 'INNER JOIN', ...}
     → extract_order()       → {'direction': 'DESC'}
     → extract_limit()       → 10
```

### Extraction Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `extract_tables()` | Find table names | query | `List[str]` |
| `extract_columns()` | Find column names | query, tables | `Dict[str, List[str]]` |
| `extract_intent()` | Determine query type | query | `str` |
| `extract_aggregation()` | Find COUNT/AVG/etc | query | `Optional[str]` |
| `extract_filters()` | Extract WHERE conditions | query, tables | `List[Dict]` |
| `extract_calculation()` | Find arithmetic ops | query, tables | `Optional[str]` |
| `extract_join()` | Detect table joins | query, tables | `Optional[Dict]` |
| `extract_order()` | Find sort direction | query | `Optional[Dict]` |
| `extract_limit()` | Extract row limit | query | `Optional[int]` |

### Main Extract Function

```python
def extract(query: str) -> Dict:
    """Pipeline: pass data step by step"""
    result = {}

    result['tables'] = extract_tables(query)
    result['columns'] = extract_columns(query, result['tables'])
    result['intent'] = extract_intent(query)
    result['aggregation'] = extract_aggregation(query)
    result['filters'] = extract_filters(query, result['tables'])
    result['calculation'] = extract_calculation(query, result['tables'])
    result['join'] = extract_join(query, result['tables'])
    result['order'] = extract_order(query)
    result['limit'] = extract_limit(query)

    return result
```

## Building Pipeline (simple_builder.py)

Each function builds ONE SQL clause:

```python
data → build_select() → "SELECT id, cgpa"
    → build_from()   → "FROM students"
    → build_join()   → "INNER JOIN courses ON..."
    → build_where()  → "WHERE year > 2020"
    → build_order()  → "ORDER BY cgpa DESC"
    → build_limit()  → "LIMIT 10"
    → "SELECT id, cgpa FROM students WHERE year > 2020 ORDER BY cgpa DESC LIMIT 10;"
```

### Building Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `build_select()` | Create SELECT clause | data | `str` |
| `build_from()` | Create FROM clause | data | `str` |
| `build_join()` | Create JOIN clause | data | `str` |
| `build_where()` | Create WHERE clause | data | `str` |
| `build_order()` | Create ORDER BY | data | `str` |
| `build_limit()` | Create LIMIT clause | data | `str` |

### Main Build Function

```python
def build(data: Dict) -> str:
    """Pipeline: build SQL step by step"""
    parts = []

    parts.append(build_select(data))
    parts.append(build_from(data))

    join = build_join(data)
    if join:
        parts.append(join)

    where = build_where(data)
    if where:
        parts.append(where)

    order = build_order(data)
    if order:
        parts.append(order)

    limit = build_limit(data)
    if limit:
        parts.append(limit)

    return ' '.join(parts) + ';'
```

## Main Converter (nlp_to_sql.py)

Simple 2-step pipeline:

```python
def convert(query: str) -> str:
    """query → extract → build → sql"""
    data = extract(query)  # Step 1: Extract
    sql = build(data)      # Step 2: Build
    return sql
```

## Supported Features

### Tables (6 core tables)
- students, employees, products, cars, orders, customers

### Query Types
- **Retrieval** - SELECT * FROM table
- **Filtering** - WHERE conditions
- **Ranking** - TOP N with ORDER BY
- **Aggregation** - COUNT, AVG, SUM, MAX, MIN
- **Calculation** - Arithmetic between columns
- **Join** - INNER JOIN between related tables

### Operators
- **LIKE** - Pattern matching
- **IN** - Multiple value matching
- **NOT IN** - Negated matching
- **BETWEEN** - Range queries
- **Comparison** - >, <, =
- **Arithmetic** - +, -, *, /

### Relationships (for JOINs)
- orders ↔ customers (via customer_id)

## Examples

### Basic Query
```
Query: "show all students"
Extract: {tables: ['students'], intent: 'retrieval', ...}
Build: SELECT * FROM students;
```

### Ranking
```
Query: "Top 10 students with highest CGPA"
Extract: {
  tables: ['students'],
  columns: {'students': ['cgpa']},
  intent: 'ranking',
  order: {'direction': 'DESC'},
  limit: 10
}
Build: SELECT students.id, students.cgpa FROM students ORDER BY cgpa DESC LIMIT 10;
```

### Aggregation
```
Query: "Average salary of employees"
Extract: {
  tables: ['employees'],
  columns: {'employees': ['salary']},
  intent: 'aggregation',
  aggregation: 'AVG'
}
Build: SELECT AVG(salary) as result FROM employees;
```

### Filtering
```
Query: "students with name like John"
Extract: {
  tables: ['students'],
  columns: {'students': ['name']},
  intent: 'filtering',
  filters: [{column: 'name', operator: 'LIKE', value: '%john%'}]
}
Build: SELECT name FROM students WHERE name LIKE '%john%';
```

### Calculation
```
Query: "salary plus bonus for employees"
Extract: {
  tables: ['employees'],
  intent: 'calculation',
  calculation: 'salary + bonus'
}
Build: SELECT salary + bonus as result FROM employees;
```

### Join
```
Query: "orders with customer name"
Extract: {
  tables: ['orders', 'customers'],
  columns: {'customers': ['name']},
  intent: 'join',
  join: {
    type: 'INNER JOIN',
    left_table: 'orders',
    right_table: 'customers',
    left_column: 'customer_id',
    right_column: 'id'
  }
}
Build: SELECT customers.name FROM orders
       INNER JOIN customers ON orders.customer_id = customers.id;
```

## Usage

### As a Module
```python
from nlp_to_sql import convert

sql = convert("Top 10 students with highest CGPA")
# SELECT students.id, students.cgpa FROM students ORDER BY cgpa DESC LIMIT 10;
```

### With Details
```python
from nlp_to_sql import convert

sql = convert("orders with customer name", verbose=True)
# Shows: tables, intent, columns, join info, final SQL
```

### Run Demo
```bash
python nlp_to_sql.py
```

### Run Tests
```bash
python test_modular.py
```

## Benefits of Modular Design

### 1. Easy to Understand
- Each function has one clear purpose
- Data flows in one direction
- No hidden dependencies

### 2. Easy to Debug
- Test each function independently
- See exactly where issues occur
- Isolate problems quickly

### 3. Easy to Extend
- Add new extraction function → just append to pipeline
- Add new SQL clause → add new build function
- Modify one part without breaking others

### 4. Easy to Test
```python
# Test individual functions
tables = extract_tables("students with high marks")
assert tables == ['students']

filters = extract_filters("salary > 50000", ['employees'])
assert filters[0]['operator'] == '>'

# Test the full pipeline
sql = convert("Top 5 products with highest price")
assert "ORDER BY" in sql and "LIMIT 5" in sql
```

### 5. Easy to Maintain
- Small functions (~10-20 lines each)
- Clear separation of concerns
- Self-documenting code

## Design Principles Applied

1. **Single Responsibility** - Each function does ONE thing
2. **Pure Functions** - Same input → same output, no side effects
3. **Composition** - Build complex behavior from simple functions
4. **Data Flow** - Information passes cleanly through pipeline
5. **Immutability** - Extract builds new dict, doesn't modify input

## Adding New Features

### Add a new operator (e.g., HAVING)

1. Add extraction function:
```python
def extract_having(query: str) -> Optional[str]:
    """Extract HAVING clause"""
    if 'having' in query.lower():
        # Extract having condition
        return condition
    return None
```

2. Add to pipeline:
```python
result['having'] = extract_having(query)
```

3. Add builder function:
```python
def build_having(data: Dict) -> str:
    """Build HAVING clause"""
    having = data.get('having')
    return f"HAVING {having}" if having else ""
```

4. Add to build pipeline:
```python
having = build_having(data)
if having:
    parts.append(having)
```

Done! Four simple steps, no rewrites needed.

## File Structure

```
simple_extractor.py (300 lines)
├── SCHEMA dictionary
├── RELATIONSHIPS dictionary
├── 9 extraction functions
└── 1 main extract() pipeline

simple_builder.py (150 lines)
├── 6 building functions
└── 1 main build() pipeline

nlp_to_sql.py (70 lines)
├── 1 convert() function
└── 1 demo main()
```

Total: ~520 lines of clean, modular code

## Summary

This modular architecture makes the codebase:
- **Simple** - Each function is small and focused
- **Readable** - Data flow is obvious
- **Testable** - Functions are independent
- **Extensible** - Easy to add features
- **Maintainable** - Changes are localized

The key insight: **Pass one thing to another** - Let data flow through a pipeline of simple, focused functions rather than building complex, tangled logic.
