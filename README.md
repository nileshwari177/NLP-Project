# NLP-to-SQL System

Convert natural language queries into SQL using fuzzy matching and AI disambiguation.

## Overview

```
Natural Language Query → Preprocessor → Extractor → Builder → SQL
```

This system converts plain English questions into SQL queries using:
- **RapidFuzz** for fuzzy string matching
- **Claude AI** for disambiguation
- **Modular pipeline** for clean architecture

### Core Modules
- **nlp_to_sql.py** - Main entry point, orchestrates the NLP-to-SQL pipeline
- **preprocessor.py** - Text preprocessing (spell check, lemmatization)
- **extractor.py** - Extracts tables, columns, filters from queries using fuzzy matching
- **builder.py** - Builds SQL from extracted components
- **ai_disambiguator.py** - Uses Claude AI to resolve ambiguous queries

### Interactive Tools
- **interactive.py** - Simple interactive query interface
- **interactive_nlp_extractor.py** - Interactive extraction testing
- **interactive_query_processor.py** - Interactive SQL building testing

### Evaluation
- **test_cases_200.py** - Test suite with 200 queries
- **simple_evaluation.py** - Evaluation framework with BLEU/ROUGE metrics
- **component_accuracy.png** - Component accuracy visualization
- **nlp_performance_scores.png** - Performance metrics visualization

---

## Installation

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Set up API key**
Create a `.env` file:
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

Get your key from [console.anthropic.com](https://console.anthropic.com/)

---

## Usage

**Interactive mode:**
```bash
python interactive.py
```

**Run evaluation:**
```bash
python simple_evaluation.py
```

**Test specific components:**
```bash
python interactive_nlp_extractor.py  # Test extraction
python interactive_query_processor.py  # Test SQL building
```

---

## Example

```
Input:  "top 10 students with highest CGPA"
Output: SELECT id, cgpa FROM students ORDER BY cgpa DESC LIMIT 10;

Input:  "average salary of employees in IT department"
Output: SELECT AVG(salary) as result FROM employees WHERE department = 'IT';

Input:  "show all products"
Output: SELECT * FROM products;
```

---

## Performance

Tested on 200 queries:
- **78.5%** Exact Match
- **91.1%** BLEU Score
- **95.4%** ROUGE-1 F1
- **100%** Success Rate
