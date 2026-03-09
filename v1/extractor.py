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
    "above": ">",
    "over": ">",
    "exceeds": ">",
    "less than": "<",
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
    "points": "marks",
    "student name": "name",
    "student": "name",
    "vehicle": "car_name",
    "vehicles": "car_name",
    "car": "car_name",
    "automobile": "car_name",
    "cost": "price",
    "value": "price",
    "amount": "price",
    "sales": "units_sold",
    "sold": "units_sold",
    "staff": "name",
    "employee name": "name",
    "worker": "name",
    "item": "product_name",
    "product": "product_name"
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

    # Detect table
    table = detect_table(query)

    # Detect specific column if mentioned
    column = detect_column(query, table)

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
        "where": where_conditions
    }


def detect_table(query):
    """Detect table name using fuzzy matching with confidence threshold."""
    # Build list of all table names and their aliases
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

    # Fuzzy match against all candidates
    match = process.extractOne(query, table_candidates, scorer=fuzz.partial_ratio)

    if match and match[1] >= TABLE_MATCH_THRESHOLD:
        matched_name = match[0]
        return table_map[matched_name]

    return None


def detect_aggregation(query):
    """Detect aggregation function with multi-word phrase support."""
    # Check multi-word phrases first (longest match wins)
    sorted_phrases = sorted(AGG_WORDS.keys(), key=len, reverse=True)

    for word in sorted_phrases:
        if word in query:
            return AGG_WORDS[word]

    return None


def detect_limit(query):
    numbers = re.findall(r'\d+', query)
    if numbers:
        return int(numbers[0])
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
    """Detect column name using fuzzy matching and synonyms."""
    if not table or table not in SCHEMA:
        return None

    columns = list(SCHEMA[table]["columns"].keys())

    # Check for exact synonym matches first
    for synonym, actual_column in COLUMN_SYNONYMS.items():
        if synonym in query and actual_column in columns:
            return actual_column

    # Fuzzy match against actual column names
    match = process.extractOne(query, columns, scorer=fuzz.partial_ratio)

    if match and match[1] >= 70:
        return match[0]

    return None


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

    # Pattern 2: Detect comparison operators with numeric values
    # Example: "price greater than 50000" or "cgpa above 3.5"
    for phrase, operator in sorted(COMPARISON_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
        if phrase in query:
            # Extract number after the comparison phrase
            pattern = rf'{re.escape(phrase)}\s+(\d+\.?\d*)'
            match = re.search(pattern, query)
            if match:
                value = match.group(1)
                # Try to find which column this applies to
                column = detect_column(query.split(phrase)[0], table)
                if column and column not in [c["column"] for c in conditions]:
                    conditions.append({
                        "column": column,
                        "operator": operator,
                        "value": value
                    })

    # Pattern 3: String equality (name/car_name filters)
    # Example: "students named John" or "car is Tesla"
    for col in columns:
        if columns[col] == "string" and col in ["name", "car_name"]:
            # Look for patterns like "named X", "called X", "car is X"
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

    # Pattern 4: Range queries (BETWEEN)
    # Example: "price between 10000 and 50000"
    between_pattern = r'between\s+(\d+\.?\d*)\s+and\s+(\d+\.?\d*)'
    between_match = re.search(between_pattern, query)
    if between_match:
        column = detect_column(query.split('between')[0], table)
        if column and column not in [c["column"] for c in conditions]:
            conditions.append({
                "column": column,
                "operator": "BETWEEN",
                "value": (between_match.group(1), between_match.group(2))
            })

    return conditions