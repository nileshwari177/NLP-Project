# NLP to SQL Query Generator

An intelligent system that converts natural language queries into SQL statements using NLP techniques, confidence scoring, AI-powered disambiguation, and comprehensive evaluation metrics.

---

## Table of Contents

- [Overview](#overview)
- [Dataset Schema](#dataset-schema)
- [System Architecture](#system-architecture)
- [Keyword Extraction & Confidence Scoring](#keyword-extraction--confidence-scoring)
- [AI-Powered Disambiguation](#ai-powered-disambiguation)
- [SQL Query Generation](#sql-query-generation)
- [Evaluation Metrics](#evaluation-metrics)
- [Performance Results](#performance-results)
- [Usage](#usage)
- [Installation](#installation)

---

## Overview

This system transforms natural language questions into executable SQL queries through a multi-stage pipeline:

```
Natural Language → Keyword Extraction → AI Disambiguation → SQL Generation → Validation
```

**Key Features:**
- Multi-table database support (10 tables with 150+ columns)
- Confidence-based keyword extraction
- AI-powered ambiguity resolution using Claude API
- Comprehensive evaluation with BLEU, ROUGE, and component accuracy metrics
- 78.5% exact match accuracy, 91.12% BLEU score

---

## Dataset Schema

The system supports a comprehensive database with **10 tables** across various domains:

### 1. Students Table
```
Columns: id, name, cgpa, marks, year, age, email, phone, address,
         enrollment_date, major, semester, gpa, attendance_percentage,
         scholarship_amount, is_active
```

### 2. Employees Table
```
Columns: id, name, email, phone, salary, department, position, year_joined,
         hire_date, rating, age, experience_years, bonus, commission,
         manager_id, office_location, is_active, employment_type
```

### 3. Cars Table
```
Columns: id, car_name, brand, model, price, units_sold, year, color,
         fuel_type, transmission, mileage, engine_capacity, horsepower,
         seats, rating, manufacturing_date, is_available
```

### 4. Products Table
```
Columns: id, product_name, brand, category, subcategory, price, cost_price,
         quantity, rating, reviews_count, weight, dimensions, color,
         manufacturer, launch_date, expiry_date, discount_percentage,
         is_available, warehouse_location
```

### 5. Orders Table
```
Columns: id, order_number, customer_id, product_id, quantity, total_amount,
         discount_amount, tax_amount, final_amount, order_date, delivery_date,
         status, payment_method, shipping_address, is_paid, is_delivered
```

### 6. Customers Table
```
Columns: id, name, email, phone, address, city, state, country, postal_code,
         registration_date, last_purchase_date, total_purchases, total_spent,
         loyalty_points, customer_tier, is_active, age, gender
```

### 7. Departments Table
```
Columns: id, department_name, department_code, manager_id, budget,
         employee_count, location, floor_number, established_date, is_active
```

### 8. Projects Table
```
Columns: id, project_name, project_code, description, manager_id,
         department_id, budget, spent_amount, start_date, end_date,
         deadline, status, priority, completion_percentage, team_size, is_active
```

### 9. Courses Table
```
Columns: id, course_name, course_code, credits, instructor_id, department,
         semester, year, max_students, enrolled_students, room_number,
         schedule, duration_hours, difficulty_level, is_active
```

### 10. Suppliers Table
```
Columns: id, supplier_name, contact_person, email, phone, address, city,
         country, rating, total_orders, total_value, payment_terms,
         delivery_time_days, is_active, registration_date
```

### Schema Metadata

Each table includes:
- **Column Types**: Numeric, string, date, boolean classifications
- **Aliases**: Alternative names (e.g., "student" → "students", "car" → "cars")
- **Sortable Columns**: Columns suitable for ORDER BY operations
- **Filterable Columns**: Columns suitable for WHERE conditions
- **Default Display Columns**: Columns shown in SELECT for retrieval queries

---

## System Architecture

### Pipeline Flow

```
┌─────────────────────┐
│  Natural Language   │
│  "Top 10 students   │
│  with highest CGPA" │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Keyword Extractor   │
│ (NLPExtractor)      │
│  • Table detection  │
│  • Column detection │
│  • Intent analysis  │
│  • Filter extraction│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Confidence Scoring  │
│  • Table: 100%      │
│  • Column: 100%     │
│  • Aggregation: N/A │
│  • Filters: N/A     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ AI Disambiguator    │
│ (Claude API)        │
│  • Resolves         │
│    ambiguities      │
│  • Validates        │
│    selections       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Query Processor     │
│  • SELECT builder   │
│  • FROM builder     │
│  • WHERE builder    │
│  • ORDER BY builder │
│  • LIMIT builder    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generated SQL       │
│ SELECT id, cgpa     │
│ FROM students       │
│ ORDER BY cgpa DESC  │
│ LIMIT 10;           │
└─────────────────────┘
```

---

## Keyword Extraction & Confidence Scoring

The `NLPExtractor` uses multi-strategy keyword detection with confidence scoring:

### 1. Table Detection

**Strategy Hierarchy:**
1. **Exact Word Match** (Confidence: 100%) - Direct table name in query
2. **Column-Based Inference** (Confidence: 80-120%) - Infers table from mentioned columns
3. **Fuzzy Matching** (Confidence: 60-100%) - RapidFuzz partial ratio matching

**Example:**
```python
Query: "Show students with high CGPA"
→ Table: "students" (Confidence: 100%, Exact match)

Query: "Maximum salary in IT department"
→ Table: "employees" (Confidence: 120%, Column "salary" found)
```

**Scoring Logic:**
```python
# Column-based scoring
for col in table_columns:
    if col in query:
        score += 120  # Numeric column match
    elif synonym_match:
        score += 100  # Synonym match

best_table = max(table_scores)  # Highest scoring table
```

### 2. Column Detection

**Strategy Hierarchy (in order):**

**Strategy 0: Exact Word Boundary Matching** (Confidence: 100%)
```python
# Prevents "age" matching in "average"
pattern = r'\b' + re.escape(column_name) + r'\b'
if re.search(pattern, query):
    primary_column = column_name
```

**Strategy 1: Aggregation Context** (Confidence: 95%)
```python
# "average marks" → extract "marks" column
# Proximity-based scoring near aggregation keywords
proximity_score = 1000 - abs(keyword_pos - column_pos)
```

**Strategy 2: Synonym Matching** (Confidence: 95%)
```python
# "price" → matches "cost", "pricing", "amount"
COLUMN_SYNONYMS = {
    "price": ["cost", "pricing", "value", "amount"],
    "salary": ["wage", "pay", "income", "compensation"]
}
```

**Strategy 3: Ranking Context** (Confidence: 90%)
```python
# "highest delivery time" → extract "delivery_time_days"
for sortable_column in sortable_columns:
    if column in query_after_ranking_keyword:
        return column
```

**Strategy 4: Fuzzy Matching** (Confidence: 70-100%)
```python
# Last resort - fuzzy string matching
result = process.extractOne(query, columns, score_cutoff=70.0)
```

### 3. Intent Classification

The system classifies queries into 4 intent types:

```python
def _determine_intent(agg_info, rank_info, filter_info):
    if rank_info['direction'] and rank_info['limit']:
        return "ranking"      # Top 10, Bottom 5, etc.
    elif agg_info['function']:
        return "aggregation"  # AVG, SUM, COUNT, MAX, MIN
    elif filter_info['conditions']:
        return "filtering"    # WHERE conditions
    else:
        return "retrieval"    # Basic SELECT queries
```

**Intent Examples:**
- **Ranking**: "Top 10 students with highest CGPA"
- **Aggregation**: "Average salary of employees"
- **Filtering**: "Students in year 2024"
- **Retrieval**: "Show all products"

### 4. Filter Extraction

**Supported Patterns:**

**Comparison Operators:**
```python
"salary > 50000"          → WHERE salary > 50000
"age less than 30"        → WHERE age < 30
"price at least 1000"     → WHERE price >= 1000
"marks greater than 80"   → WHERE marks > 80
```

**String Filters:**
```python
"in IT department"              → WHERE department = 'IT'
"from city Mumbai"              → WHERE city = 'Mumbai'
"in Electronics category"       → WHERE category = 'Electronics'
"in year 2024"                  → WHERE year = '2024'
```

**Range Filters:**
```python
"age between 20 and 30"   → WHERE age BETWEEN 20 AND 30
```

### Confidence Score Summary

```
Component          Strategy             Confidence Range
─────────────────────────────────────────────────────────
Table Detection    Exact Match          100%
                   Column Inference     80-120%
                   Fuzzy Match          60-100%

Column Detection   Exact Boundary       100%
                   Aggregation Context  95%
                   Synonym Match        95%
                   Ranking Context      90%
                   Fuzzy Match          70-100%

Filter Extraction  Direct Pattern       85-95%
                   Department Filter    85%
                   City Filter          85%
                   Year Filter          90%

Aggregation        Keyword Match        95%
```

---

## AI-Powered Disambiguation

When keyword extraction confidence is low or results are ambiguous, the system uses **Claude AI** for disambiguation.

### AIDisambiguator Class

**Triggers for AI Disambiguation:**
1. Low confidence scores (< 70%)
2. Multiple possible interpretations
3. Complex or ambiguous queries
4. User-requested clarification

**Process:**

```python
class AIDisambiguator:
    def disambiguate(self, query, keywords, schema_info):
        """
        Uses Claude AI to resolve ambiguities

        Args:
            query: Natural language query
            keywords: Extracted keywords with confidence scores
            schema_info: Available tables and columns

        Returns:
            Refined keywords with high confidence
        """
        prompt = self._build_disambiguation_prompt(
            query, keywords, schema_info
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_ai_response(response)
```

**Example Disambiguation:**

```
User Query: "Show employees in IT"

Ambiguity: Does "IT" refer to:
  - department = 'IT'
  - position containing 'IT'
  - office_location = 'IT' (Italy)

AI Analysis:
  Context: "employees in IT" → most likely department
  Confidence: 95%
  Resolution: department = 'IT'
```

**AI Prompt Structure:**

```
You are helping disambiguate a natural language query for SQL generation.

Query: "{natural_language_query}"

Extracted Information:
- Table: {table_name} (Confidence: {confidence}%)
- Column: {column_name} (Confidence: {confidence}%)
- Intent: {intent}

Available Schema:
{schema_structure}

Ambiguities:
{list_of_ambiguities}

Please provide:
1. Most likely interpretation
2. Confidence level
3. Alternative interpretations (if any)
```

---

## SQL Query Generation

The `QueryProcessor` builds SQL queries from extracted keywords:

### SELECT Clause Builder

**Logic Flow:**

```python
def _build_select(keywords):
    intent = keywords['intent']
    column = keywords['primary_column']
    aggregation = keywords['aggregation']

    if intent == 'ranking':
        # Show ID + ranking column
        return f"SELECT id, {column}"

    elif intent == 'aggregation':
        if aggregation == 'COUNT':
            return "SELECT COUNT(id) as result"
        else:
            return f"SELECT {aggregation}({column}) as result"

    elif intent in ['filtering', 'retrieval']:
        if 'all' in query:
            return "SELECT *"  # Show all columns
        elif explicit_column_request:
            return f"SELECT {column}"  # Specific column
        else:
            return "SELECT *"  # Default to all columns

    else:
        return f"SELECT {column}"
```

**Examples:**

```sql
-- Ranking Intent
Query: "Top 10 students with highest CGPA"
→ SELECT id, cgpa

-- Aggregation Intent
Query: "Average salary of employees"
→ SELECT AVG(salary) as result

-- Filtering Intent
Query: "Students in year 2024"
→ SELECT *

-- Retrieval Intent
Query: "Show all products"
→ SELECT *
```

### FROM Clause Builder

```python
def _build_from(keywords):
    return f"FROM {keywords['table']}"
```

### WHERE Clause Builder

```python
def _build_where(keywords):
    filters = keywords['filters']
    if not filters:
        return ""

    conditions = []
    for filter_item in filters:
        column = filter_item['column']
        operator = filter_item['operator']
        value = filter_item['value']

        if operator == 'BETWEEN':
            conditions.append(
                f"{column} BETWEEN {value[0]} AND {value[1]}"
            )
        elif filter_item['type'] == 'string':
            conditions.append(
                f"{column} {operator} '{value}'"
            )
        else:
            conditions.append(
                f"{column} {operator} {value}"
            )

    return "WHERE " + " AND ".join(conditions)
```

### ORDER BY Clause Builder

```python
def _build_order(keywords):
    direction = keywords['ranking_direction']
    column = keywords['primary_column']
    intent = keywords['intent']

    # Only add ORDER BY for ranking queries
    # Aggregations like MAX/MIN don't need ORDER BY
    if direction and column and intent == 'ranking':
        return f"ORDER BY {column} {direction}"

    return ""
```

### LIMIT Clause Builder

```python
def _build_limit(keywords):
    limit = keywords['limit']

    if limit:
        return f"LIMIT {limit}"

    return ""
```

### Complete Query Assembly

```python
def process(keywords):
    sql_parts = [
        _build_select(keywords),    # SELECT clause
        _build_from(keywords),       # FROM clause
        _build_where(keywords),      # WHERE clause (optional)
        _build_order(keywords),      # ORDER BY clause (optional)
        _build_limit(keywords)       # LIMIT clause (optional)
    ]

    # Filter out empty parts and join with space
    sql = ' '.join([part for part in sql_parts if part])

    return sql + ';'
```

---

## Evaluation Metrics

The system uses multiple metrics to measure accuracy and quality:

### 1. BLEU Score (Bilingual Evaluation Understudy)

**Purpose:** Measures n-gram overlap between generated and expected SQL

**Calculation:**
```python
def calculate_bleu(reference, candidate, max_n=4):
    """
    BLEU = BP × exp(Σ w_n × log p_n)

    where:
    - BP = Brevity Penalty
    - p_n = Precision for n-grams (n=1,2,3,4)
    - w_n = Weight for each n-gram (usually 1/4)
    """
    bleu_scores = {}

    for n in range(1, max_n + 1):
        precision = calculate_ngram_precision(reference, candidate, n)
        bleu_scores[f'bleu_{n}'] = precision

    # Overall BLEU = geometric mean of precisions
    bleu_scores['bleu'] = geometric_mean(bleu_scores.values())

    return bleu_scores
```

**Example:**
```python
Reference:  "SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;"
Candidate:  "SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;"

BLEU-1: 1.000  # All 1-grams match
BLEU-2: 1.000  # All 2-grams match
BLEU-3: 1.000  # All 3-grams match
BLEU-4: 1.000  # All 4-grams match
Overall BLEU: 1.000 (100% perfect match)
```

**Interpretation:**
- **0.9 - 1.0**: Excellent (Near-perfect match)
- **0.8 - 0.9**: Good (High quality with minor differences)
- **0.6 - 0.8**: Moderate (Functional but different syntax)
- **< 0.6**: Poor (Significant differences)

### 2. ROUGE Scores (Recall-Oriented Understudy for Gisting Evaluation)

**Purpose:** Measures recall and F1 score for token overlap

**Variants:**

**ROUGE-1** (Unigram overlap):
```python
Precision = matching_unigrams / total_candidate_unigrams
Recall    = matching_unigrams / total_reference_unigrams
F1        = 2 × (Precision × Recall) / (Precision + Recall)
```

**ROUGE-2** (Bigram overlap):
```python
Precision = matching_bigrams / total_candidate_bigrams
Recall    = matching_bigrams / total_reference_bigrams
F1        = 2 × (Precision × Recall) / (Precision + Recall)
```

**ROUGE-L** (Longest Common Subsequence):
```python
LCS_length = longest_common_subsequence(reference, candidate)
Precision  = LCS_length / len(candidate)
Recall     = LCS_length / len(reference)
F1         = 2 × (Precision × Recall) / (Precision + Recall)
```

**Example:**
```python
Reference:  "SELECT AVG(salary) FROM employees WHERE department = 'IT';"
Candidate:  "SELECT AVG(salary) FROM employees WHERE department = 'IT';"

ROUGE-1: Precision=1.00, Recall=1.00, F1=1.00
ROUGE-2: Precision=1.00, Recall=1.00, F1=1.00
ROUGE-L: Precision=1.00, Recall=1.00, F1=1.00
```

### 3. Exact Match

**Purpose:** Binary metric for perfect SQL match

```python
def exact_match(reference, candidate):
    # Normalize whitespace and case
    ref_normalized = ' '.join(reference.strip().upper().split())
    cand_normalized = ' '.join(candidate.strip().upper().split())

    return 1.0 if ref_normalized == cand_normalized else 0.0
```

**Example:**
```python
Reference:  "SELECT * FROM students;"
Candidate:  "SELECT  *  FROM  students  ;"  # Extra spaces

Exact Match: 1.0 (normalized to same)
```

### 4. Component-wise Accuracy

**Purpose:** Measures accuracy of individual SQL components

```python
def component_accuracy(reference, candidate):
    """
    Checks accuracy of each SQL clause separately:
    - SELECT clause
    - FROM clause
    - WHERE clause
    - ORDER BY clause
    - LIMIT clause
    """

    components = {
        'select_accuracy': compare_select_clause(ref, cand),
        'from_accuracy': compare_from_clause(ref, cand),
        'where_accuracy': compare_where_clause(ref, cand),
        'order_by_accuracy': compare_order_clause(ref, cand),
        'limit_accuracy': compare_limit_clause(ref, cand)
    }

    # Overall component accuracy
    components['overall_component_accuracy'] = mean(components.values())

    return components
```

**Example:**
```python
Reference:  "SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;"
Candidate:  "SELECT id, gpa FROM students ORDER BY gpa DESC LIMIT 10;"

Component Accuracy:
  SELECT:   0.50  # id matches, cgpa→gpa doesn't
  FROM:     1.00  # students matches
  WHERE:    1.00  # Both have no WHERE
  ORDER BY: 0.50  # Structure matches, column differs
  LIMIT:    1.00  # 10 matches
  Overall:  0.80  # 80% component accuracy
```

### 5. Similarity Ratio

**Purpose:** Character-level similarity using RapidFuzz

```python
def similarity_ratio(reference, candidate):
    return fuzz.ratio(reference.strip(), candidate.strip()) / 100.0
```

**Example:**
```python
Reference:  "SELECT * FROM students WHERE year = '2024';"
Candidate:  "SELECT * FROM students WHERE year = '2023';"

Similarity: 0.9756 (97.56% character similarity)
```

### Aggregated Metrics

The evaluation framework aggregates metrics across all test cases:

```python
def aggregate_results(all_metrics):
    """
    Aggregates metrics across all test cases

    Returns:
        {
            'avg_bleu': mean BLEU score,
            'avg_rouge_1_f1': mean ROUGE-1 F1,
            'avg_rouge_l_f1': mean ROUGE-L F1,
            'avg_exact_match': exact match rate,
            'avg_similarity_ratio': mean similarity,
            'avg_overall_component_accuracy': mean component accuracy,
            'avg_select_accuracy': mean SELECT accuracy,
            'avg_from_accuracy': mean FROM accuracy,
            'avg_where_accuracy': mean WHERE accuracy,
            'avg_order_by_accuracy': mean ORDER BY accuracy,
            'avg_limit_accuracy': mean LIMIT accuracy
        }
    """
```

---

## Performance Results

### Overall Metrics (200 Test Cases)

```
┌─────────────────────────────┬──────────┐
│ Metric                      │ Score    │
├─────────────────────────────┼──────────┤
│ Exact Match Rate            │  78.50%  │
│ BLEU Score                  │  91.12%  │
│ ROUGE-1 F1                  │  95.43%  │
│ ROUGE-L F1                  │  94.97%  │
│ Similarity Ratio            │  95.05%  │
│ Overall Component Accuracy  │  89.80%  │
│ Success Rate                │ 100.00%  │
└─────────────────────────────┴──────────┘
```

### Component-wise Accuracy

```
┌──────────────┬──────────┐
│ Component    │ Accuracy │
├──────────────┼──────────┤
│ SELECT       │  87.50%  │
│ FROM         │  94.50%  │
│ WHERE        │  70.13%  │
│ ORDER BY     │  93.15%  │
│ LIMIT        │ 100.00%  │
└──────────────┴──────────┘
```

### Performance by Category

```
┌────────────────────────────┬────────────┬──────────────┐
│ Category                   │ BLEU Score │ Exact Match  │
├────────────────────────────┼────────────┼──────────────┤
│ Basic Retrieval            │   96.0%    │    96.0%     │
│ Ranking                    │  100.0%    │   100.0%     │ ⭐
│ Aggregation                │   90.0%    │    69.4%     │
│ Filtering                  │   80.4%    │    76.5%     │
│ Complex Queries            │   93.9%    │    90.0%     │
│ Complex Filtering + Agg    │   96.3%    │    61.5%     │
│ Complex Filtering + Rank   │   79.5%    │    35.0%     │
└────────────────────────────┴────────────┴──────────────┘
```

### Performance by Difficulty

```
┌────────────┬────────────┬──────────────┐
│ Difficulty │ BLEU Score │ Exact Match  │
├────────────┼────────────┼──────────────┤
│ Easy       │   96.0%    │    96.0%     │
│ Medium     │   91.2%    │    82.6%     │
│ Hard       │   87.9%    │    55.8%     │
└────────────┴────────────┴──────────────┘
```

### Test Statistics

```
Total Test Cases:       200
Successful Tests:       200 (100.0%)
Failed Tests:           0
Exact Matches:          157 (78.5%)
High Quality (>80%):    170 (85.0%)
```

### Example Success Cases

**✅ Basic Retrieval:**
```
Query:     "Show all students"
Expected:  SELECT * FROM students;
Generated: SELECT * FROM students;
BLEU:      1.000 ✓
```

**✅ Ranking:**
```
Query:     "Top 10 students with highest CGPA"
Expected:  SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;
Generated: SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;
BLEU:      1.000 ✓
```

**✅ Aggregation:**
```
Query:     "Average salary of employees"
Expected:  SELECT AVG(salary) as result FROM employees;
Generated: SELECT AVG(salary) as result FROM employees;
BLEU:      1.000 ✓
```

**✅ Filtering:**
```
Query:     "Students in year 2024"
Expected:  SELECT * FROM students WHERE year = '2024';
Generated: SELECT * FROM students WHERE year = '2024';
BLEU:      1.000 ✓
```

**✅ Complex Query:**
```
Query:     "Top 5 employees with highest salary in IT department"
Expected:  SELECT id, salary FROM employees WHERE department = 'IT'
           ORDER BY salary DESC LIMIT 5;
Generated: SELECT id, salary FROM employees WHERE department = 'IT'
           ORDER BY salary DESC LIMIT 5;
BLEU:      1.000 ✓
```

---

## Usage

### Interactive Application

Run the interactive web application:

```bash
python interactive_app.py
```

**Features:**
- Real-time query conversion
- Step-by-step visualization of the pipeline
- Confidence score display
- AI disambiguation interface

### Command Line Testing

Test a single query:

```bash
python -c "
from interactive_nlp_extractor import NLPExtractor
from interactive_query_processor import QueryProcessor

extractor = NLPExtractor()
processor = QueryProcessor()

query = 'Show top 10 students with highest CGPA'
keywords = extractor.extract_keywords(query)
sql = processor.process(keywords)

print(f'Query: {query}')
print(f'SQL: {sql}')
"
```

### Running Evaluation

Evaluate on the test dataset:

```bash
# Run full evaluation with visualizations
python run_evaluation.py --dataset test_dataset_200.json

# Run evaluation without visualizations
python run_evaluation.py --dataset test_dataset_200.json --no-viz

# Generate new test dataset
python run_evaluation.py --generate 100 --dataset new_dataset.json

# Specify custom output directory
python run_evaluation.py --dataset test_dataset_200.json --output my_results
```

**Output Files:**
```
evaluation_results/
├── evaluation_results.json          # Detailed results
├── evaluation_summary.txt           # Summary report
├── overall_metrics.png              # Metrics comparison chart
├── component_accuracy.png           # Component accuracy chart
├── category_performance.png         # Category breakdown chart
├── difficulty_performance.png       # Difficulty analysis chart
└── comprehensive_dashboard.png      # Complete dashboard
```

### Generating Test Datasets

Create custom test datasets:

```python
from dataset_generator import DatasetGenerator

generator = DatasetGenerator()

# Generate 100 test cases
dataset = generator.generate_samples(num_samples=100)

# Save to file
generator.save_to_file(dataset, 'my_dataset.json')
```

**Dataset Structure:**
```json
{
  "test_cases": [
    {
      "id": 1,
      "category": "basic_retrieval",
      "difficulty": "easy",
      "natural_language": "Show all students",
      "expected_sql": "SELECT * FROM students;",
      "keywords": ["show", "all", "students"]
    },
    ...
  ],
  "metadata": {
    "total_cases": 100,
    "generated_at": "2026-03-24T12:00:00"
  }
}
```

---

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Required Packages:**
```
anthropic>=0.40.0        # Claude AI API
rapidfuzz>=3.0.0         # Fuzzy string matching
matplotlib>=3.7.0        # Visualization
seaborn>=0.12.0          # Statistical visualization
pandas>=2.0.0            # Data manipulation
numpy>=1.24.0            # Numerical operations
```

### Environment Setup

Create a `.env` file for API credentials:

```bash
# .env file
ANTHROPIC_API_KEY=your_api_key_here
```

**Get your API key:**
1. Visit https://console.anthropic.com/
2. Create an account or log in
3. Navigate to API Keys section
4. Generate a new API key
5. Copy to `.env` file

### Project Structure

```
NLP-Project/
├── interactive_app.py                    # Main web application
├── interactive_nlp_extractor.py          # Keyword extraction
├── interactive_query_processor.py        # SQL generation
├── ai_disambiguator.py                   # AI-powered disambiguation
├── evaluation_framework.py               # Evaluation orchestrator
├── evaluation_metrics.py                 # Metrics calculation
├── visualization.py                      # Chart generation
├── dataset_generator.py                  # Test data generation
├── run_evaluation.py                     # Evaluation script
├── test_dataset_200.json                 # Test dataset (200 cases)
├── requirements.txt                      # Python dependencies
├── .env                                  # API credentials
└── evaluation_results_200_final/         # Latest results
    ├── evaluation_results.json
    ├── evaluation_summary.txt
    └── *.png (visualizations)
```

---

## Key Technical Highlights

### 1. Word Boundary Matching
Prevents "age" from matching in "aver**age**" using regex `\b`:
```python
pattern = r'\b' + re.escape(column_name) + r'\b'
```

### 2. Intent Prioritization
Ranking takes precedence when limit is present:
```python
if direction and limit:
    return "ranking"  # Not aggregation
```

### 3. Dynamic Pattern Generation
Supports all table names dynamically:
```python
table_pattern = '|'.join(re.escape(term) for term in all_tables)
```

### 4. Proximity-based Scoring
Selects columns closest to aggregation keywords:
```python
proximity_score = 1000 - abs(keyword_pos - column_pos)
```

### 5. Normalization
Handles underscores in column names:
```python
col_normalized = col.replace('_', ' ')
# "completion_percentage" matches "completion percentage"
```

---

## Future Enhancements

- [ ] Support for JOIN operations
- [ ] GROUP BY and HAVING clauses
- [ ] Subquery generation
- [ ] Multiple table queries
- [ ] Advanced WHERE conditions (OR, IN, LIKE)
- [ ] Query optimization
- [ ] Machine learning-based column prediction
- [ ] User feedback integration
- [ ] Real database connection
- [ ] Query execution and result display

---

## License

MIT License - See LICENSE file for details

---

## Contributors

- Development Team: NLP-Project Contributors
- Evaluation Framework: Comprehensive metrics system
- AI Integration: Claude API by Anthropic

---

## Support

For issues, questions, or contributions:
- Create an issue in the repository
- Review the evaluation results in `evaluation_results_200_final/`
- Check the test dataset in `test_dataset_200.json`

---

**Version:** 2.0
**Last Updated:** March 24, 2026
**Status:** ✅ Production Ready
**Accuracy:** 78.5% Exact Match, 91.12% BLEU Score
