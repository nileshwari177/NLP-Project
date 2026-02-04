import re
from rapidfuzz import process
from schema_registry import SCHEMA

RANK_WORDS = ["top", "highest", "best"]
BOTTOM_WORDS = ["bottom", "lowest", "worst"]

AGG_WORDS = {
    "average": "AVG",
    "avg": "AVG",
    "total": "SUM",
    "sum": "SUM",
    "count": "COUNT"
}


def extract_entities(query: str):
    query = query.lower()

    tokens = query.split()

    # Detect table
    table = detect_table(query)

    # Detect aggregation
    aggregation = detect_aggregation(query)

    # Detect limit
    limit = detect_limit(query)

    # Detect ordering direction
    direction = detect_direction(query)

    # Detect numeric filter (like year = 2024)
    where_conditions = detect_where_conditions(query, table)

    return {
        "table": table,
        "aggregation": aggregation,
        "limit": limit,
        "direction": direction,
        "where": where_conditions
    }


def detect_table(query):
    tables = list(SCHEMA.keys())
    match = process.extractOne(query, tables)
    if match:
        return match[0]
    return None


def detect_aggregation(query):
    for word, func in AGG_WORDS.items():
        if word in query:
            return func
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


def detect_where_conditions(query, table):
    conditions = []

    if not table:
        return conditions

    columns = SCHEMA[table]["columns"]

    # Detect year filter like 2024
    year_match = re.findall(r'(20\d{2})', query)
    if year_match and "year" in columns:
        conditions.append({
            "column": "year",
            "operator": "=",
            "value": year_match[0]
        })

    return conditions