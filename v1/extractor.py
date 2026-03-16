import re
from rapidfuzz import process, fuzz
from schema_registry import SCHEMA

RANK_WORDS = [
    "top", "highest", "best", "maximum", "max", "largest", "greatest",
    "most", "upper", "leading", "premier", "first", "foremost"
]

BOTTOM_WORDS = [
    "bottom", "lowest", "worst", "minimum", "min", "smallest", "least",
    "fewest", "lower", "last", "weakest"
]

AGG_WORDS = {
    "average": "AVG",
    "avg": "AVG",
    "mean": "AVG",
    "total": "SUM",
    "sum": "SUM",
    "add": "SUM",
    "count": "COUNT",
    "number": "COUNT",
    "how many": "COUNT",
    "maximum": "MAX",
    "max": "MAX",
    "highest": "MAX",
    "minimum": "MIN",
    "min": "MIN",
    "lowest": "MIN"
}

COMPARISON_KEYWORDS = {
    "greater than": ">",
    "more than": ">",
    "is above": ">",
    "above": ">",
    "over": ">",
    "exceeds": ">",
    "less than": "<",
    "is below": "<",
    "below": "<",
    "under": "<",
    "fewer than": "<",
    "equal to": "=",
    "equals": "=",
    "is": "=",
    "not equal to": "!=",
    "not": "!=",
    "at least": ">=",
    "minimum of": ">=",
    "at most": "<=",
    "maximum of": "<=",
    "no more than": "<="
}

COLUMN_SYNONYMS = {
    "gpa": "cgpa",
    "grade": "cgpa",
    "grade point": "cgpa",
    "score": "marks",
    "scores": "marks",
    "points": "marks",
    "mark": "marks",
    "student name": "name",
    "student": "name",
    "vehicle": "car_name",
    "vehicles": "car_name",
    "car": "car_name",
    "automobile": "car_name",
    "cost": "price",
    "costing": "price",
    "value": "price",
    "amount": "price",
    "sales": "units_sold",
    "sold": "units_sold",
    "units": "units_sold",
    "staff": "name",
    "employee name": "name",
    "worker": "name",
    "item": "product_name",
    "product": "product_name",
    "performers": "marks",
    "performer": "marks",
    "qty": "quantity",
    "stock": "quantity"
}

# Fuzzy matching threshold for table detection
TABLE_MATCH_THRESHOLD = 60


def validate_query(query):
    """Validate input query before processing."""
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    if len(query.strip()) == 0:
        raise ValueError("Query cannot be empty or whitespace only")

    if len(query) > 500:
        raise ValueError("Query is too long (max 500 characters)")

    return True


def extract_entities(query: str):
    """Extract entities from natural language query with validation."""
    # Validate input
    validate_query(query)

    original_query = query
    query = query.lower()

    # Detect table with confidence
    table, table_conf = detect_table(query)

    # Detect specific column if mentioned with confidence
    column, col_conf = detect_column(query, table)

    # Detect aggregation
    aggregation = detect_aggregation(query)

    # Detect limit
    limit = detect_limit(query)

    # Detect ordering direction
    direction = detect_direction(query)

    # Detect WHERE conditions
    where_conditions = detect_where_conditions(query, table)

    return {
        "table": table,
        "column": column,
        "aggregation": aggregation,
        "limit": limit,
        "direction": direction,
        "where": where_conditions,
        "_confidence": {
            "table": table_conf,
            "column": col_conf
        }
    }


def detect_table(query):
    """Detect table name using fuzzy matching with confidence threshold.

    Returns tuple: (table_name, confidence_score)
    """
    # Strategy 1: Check for explicit table name or alias mentions first
    table_candidates = []
    table_map = {}  # Maps candidate name to actual table name

    for table, info in SCHEMA.items():
        table_candidates.append(table)
        table_map[table] = table

        # Add aliases if they exist
        if "aliases" in info:
            for alias in info["aliases"]:
                table_candidates.append(alias)
                table_map[alias] = table

    # Check for exact matches or very high confidence fuzzy matches
    match = process.extractOne(query, table_candidates, scorer=fuzz.partial_ratio)

    if match and match[1] >= 85:  # High confidence match
        matched_name = match[0]
        confidence = match[1]
        return table_map[matched_name], confidence

    # Strategy 2: Use context-based table hints for ambiguous cases
    # Note: Only use unique keywords to avoid conflicts
    table_hints = {
        "students": ["marks", "cgpa", "gpa", "grade", "performers", "performer"],
        "cars": ["car", "vehicle", "units_sold", "units"],
        "employees": ["salary", "employee", "staff", "worker", "department"],
        "products": ["product", "item", "quantity", "category"]
    }

    # Check for strong contextual hints
    for table, keywords in table_hints.items():
        for keyword in keywords:
            if keyword in query and table in SCHEMA:
                return table, 100

    # Strategy 3: Lower confidence fuzzy match as fallback
    if match and match[1] >= TABLE_MATCH_THRESHOLD:
        matched_name = match[0]
        confidence = match[1]
        return table_map[matched_name], confidence

    return None, 0


def detect_aggregation(query):
    """Detect aggregation function with multi-word phrase support.

    NOTE: "top N" queries should NOT use aggregation - they use ORDER BY + LIMIT instead.
    """
    # Check if this is a ranking query (top/bottom N) - these are NOT aggregations
    ranking_patterns = [r'top\s+\d+', r'bottom\s+\d+', r'best\s+\d+', r'worst\s+\d+',
                       r'first\s+\d+', r'last\s+\d+', r'highest\s+\d+', r'lowest\s+\d+']

    for pattern in ranking_patterns:
        if re.search(pattern, query):
            return None  # This is a ranking query, not an aggregation

    # Check multi-word phrases first (longest match wins)
    sorted_phrases = sorted(AGG_WORDS.keys(), key=len, reverse=True)

    for word in sorted_phrases:
        if word in query:
            return AGG_WORDS[word]

    return None


def detect_limit(query):
    """Detect LIMIT from ranking phrases, not from WHERE conditions."""
    # Look for "top N", "first N", "best N", etc.
    rank_patterns = [
        r'top\s+(\d+)',
        r'first\s+(\d+)',
        r'best\s+(\d+)',
        r'worst\s+(\d+)',
        r'bottom\s+(\d+)',
        r'last\s+(\d+)',
        r'limit\s+(\d+)'
    ]

    for pattern in rank_patterns:
        match = re.search(pattern, query)
        if match:
            return int(match.group(1))

    return None


def detect_direction(query):
    for word in RANK_WORDS:
        if word in query:
            return "DESC"

    for word in BOTTOM_WORDS:
        if word in query:
            return "ASC"

    return None


def detect_column(query, table):
    """Detect column name using context-aware matching.

    Returns tuple: (column_name, confidence_score)
    """
    if not table or table not in SCHEMA:
        return None, 0

    columns = list(SCHEMA[table]["columns"].keys())

    # Strategy 1: Check for exact column name mentions
    for col in columns:
        # Use word boundaries to avoid partial matches
        if re.search(rf'\b{col}\b', query):
            return col, 100

    # Strategy 2: Check aggregation context (e.g., "average marks", "maximum price")
    agg_patterns = [
        r'average\s+(\w+)',
        r'avg\s+(\w+)',
        r'mean\s+(\w+)',
        r'total\s+(\w+)',
        r'sum\s+of\s+(\w+)',
        r'maximum\s+(\w+)',
        r'max\s+(\w+)',
        r'minimum\s+(\w+)',
        r'min\s+(\w+)',
        r'count\s+(?:of\s+)?(\w+)',
        r'highest\s+(\w+)',
        r'lowest\s+(\w+)'
    ]

    for pattern in agg_patterns:
        match = re.search(pattern, query)
        if match:
            col_word = match.group(1)
            # Check if this word matches a column (with synonyms)
            if col_word in COLUMN_SYNONYMS and COLUMN_SYNONYMS[col_word] in columns:
                return COLUMN_SYNONYMS[col_word], 100
            if col_word in columns:
                return col_word, 100

    # Strategy 3: Check for synonym matches
    for synonym, actual_column in COLUMN_SYNONYMS.items():
        if synonym in query and actual_column in columns:
            return actual_column, 95

    # Strategy 4: Context from comparison operators
    # Example: "price greater than 50000" or "rating between 4 and 5"
    for phrase in COMPARISON_KEYWORDS.keys():
        if phrase in query:
            before_phrase = query.split(phrase)[0]
            # Look for column names in the part before the operator
            for col in columns:
                if col in before_phrase or (col in COLUMN_SYNONYMS.values() and
                    any(syn in before_phrase for syn, actual in COLUMN_SYNONYMS.items() if actual == col)):
                    return col, 90

    # Strategy 5: Fuzzy match as last resort
    match = process.extractOne(query, columns, scorer=fuzz.partial_ratio)

    if match and match[1] >= 70:
        return match[0], match[1]

    return None, 0


def detect_where_conditions(query, table):
    """Enhanced WHERE condition detection with multiple operators and column types."""
    conditions = []

    if not table or table not in SCHEMA:
        return conditions

    columns = SCHEMA[table]["columns"]

    # Pattern 1: Year filter (2020-2099)
    year_match = re.findall(r'(20\d{2})', query)
    if year_match and "year" in columns:
        conditions.append({
            "column": "year",
            "operator": "=",
            "value": year_match[0]
        })

    # Pattern 2: Range queries (BETWEEN) - check this first to avoid double detection
    # Example: "rating between 4.0 and 5.0"
    between_pattern = r'(\w+)\s+between\s+(\d+\.?\d*)\s+and\s+(\d+\.?\d*)'
    between_match = re.search(between_pattern, query)
    if between_match:
        col_candidate = between_match.group(1)
        # Check if it's a column or synonym
        column_name = None
        if col_candidate in columns:
            column_name = col_candidate
        elif col_candidate in COLUMN_SYNONYMS and COLUMN_SYNONYMS[col_candidate] in columns:
            column_name = COLUMN_SYNONYMS[col_candidate]

        if column_name and column_name not in [c["column"] for c in conditions]:
            conditions.append({
                "column": column_name,
                "operator": "BETWEEN",
                "value": (between_match.group(2), between_match.group(3))
            })

    # Pattern 3: Detect comparison operators with numeric values
    # Example: "price greater than 50000" or "salary less than 50000"
    for phrase, operator in sorted(COMPARISON_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
        if phrase in query:
            # Look for: "column_name comparison_phrase number"
            pattern = rf'(\w+)\s+{re.escape(phrase)}\s+(\d+\.?\d*)'
            match = re.search(pattern, query)
            if match:
                col_candidate = match.group(1)
                value = match.group(2)

                # Check if it's a column or synonym
                column_name = None
                if col_candidate in columns:
                    column_name = col_candidate
                elif col_candidate in COLUMN_SYNONYMS and COLUMN_SYNONYMS[col_candidate] in columns:
                    column_name = COLUMN_SYNONYMS[col_candidate]

                if column_name and column_name not in [c["column"] for c in conditions]:
                    conditions.append({
                        "column": column_name,
                        "operator": operator,
                        "value": value
                    })
                    break  # Only match once per phrase

    # Pattern 4: String equality for department/category filters
    # Example: "employees in department Engineering" or "products in category Electronics"
    for col in columns:
        if columns[col] == "string" and col in ["department", "category"]:
            # Pattern: "in {column_name} {value}"
            pattern = rf'in\s+{col}\s+([A-Z][a-zA-Z]*)'
            match = re.search(pattern, query, re.IGNORECASE)
            if match and col not in [c["column"] for c in conditions]:
                conditions.append({
                    "column": col,
                    "operator": "=",
                    "value": f"'{match.group(1)}'"
                })

    # Pattern 5: String equality (name filters)
    # Example: "students named John" or "car is Tesla"
    for col in columns:
        if columns[col] == "string" and col in ["name", "car_name", "product_name"]:
            # Look for patterns like "named X", "called X", "is X"
            patterns = [
                rf'named?\s+([A-Z][a-z]+)',
                rf'called\s+([A-Z][a-z]+)',
                rf'{col}\s+is\s+([A-Z][a-z]+)',
                rf'{col}\s+equals?\s+([A-Z][a-z]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match and col not in [c["column"] for c in conditions]:
                    conditions.append({
                        "column": col,
                        "operator": "=",
                        "value": f"'{match.group(1)}'"
                    })
                    break

    return conditions