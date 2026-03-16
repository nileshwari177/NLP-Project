from schema_registry import SCHEMA
from config import Config


class AmbiguityResult:
    """Structured result containing ambiguity information."""

    def __init__(self):
        self.is_ambiguous = False
        self.ambiguity_types = []
        self.alternatives = {}
        self.confidence_scores = {}


def detect_ambiguities(entities: dict, query: str) -> AmbiguityResult:
    """
    Main ambiguity detection function.

    Detects various types of ambiguities:
    1. Low table confidence
    2. Missing ranking column
    3. Column-query mismatch
    4. Aggregation without column
    5. Multiple metrics available
    """
    result = AmbiguityResult()

    # Extract confidence scores
    if "_confidence" in entities:
        result.confidence_scores = entities["_confidence"]

    # Run all detection checks
    check_table_confidence(entities, result)
    check_missing_ranking_column(entities, query, result)
    check_aggregation_without_column(entities, query, result)
    check_column_query_mismatch(entities, query, result)

    # Set is_ambiguous flag if any ambiguities detected
    result.is_ambiguous = len(result.ambiguity_types) > 0

    return result


def check_table_confidence(entities: dict, result: AmbiguityResult):
    """Check if table match confidence is below threshold."""
    if "_confidence" not in entities:
        return

    table_conf = entities["_confidence"].get("table", 100)

    if table_conf < Config.CONFIDENCE_THRESHOLD_TABLE and table_conf > 0:
        result.ambiguity_types.append("low_table_confidence")
        result.alternatives["table"] = f"Matched with {table_conf}% confidence"


def check_missing_ranking_column(entities: dict, query: str, result: AmbiguityResult):
    """
    Detect ranking queries without explicit column.

    Examples:
    - "top 10 cars" (no column mentioned)
    - "best 5 employees" (no column mentioned)
    """
    has_limit = entities.get("limit") is not None
    has_direction = entities.get("direction") is not None
    column = entities.get("column")
    table = entities.get("table")

    # If we have ranking but no column, this is ambiguous
    if has_limit and has_direction and not column and table:
        # Get available numeric columns from schema
        if table in SCHEMA:
            columns = SCHEMA[table]["columns"]
            numeric_columns = [
                col for col, col_type in columns.items()
                if col_type in ["integer", "float"] and col != "id"
            ]

            if len(numeric_columns) > 1:
                result.ambiguity_types.append("missing_ranking_column")
                result.alternatives["column"] = numeric_columns


def check_aggregation_without_column(entities: dict, query: str, result: AmbiguityResult):
    """
    Detect aggregation queries without proper column.

    Examples:
    - "average marks" but column detected as "name"
    - "maximum price" but column detected incorrectly
    """
    aggregation = entities.get("aggregation")
    column = entities.get("column")
    table = entities.get("table")

    if not aggregation or not table:
        return

    # Get available numeric columns
    if table in SCHEMA:
        columns = SCHEMA[table]["columns"]
        numeric_columns = [
            col for col, col_type in columns.items()
            if col_type in ["integer", "float"] and col != "id"
        ]

        # If column is not numeric or column is missing, this is ambiguous
        if not column or column not in numeric_columns:
            result.ambiguity_types.append("aggregation_without_column")
            result.alternatives["column"] = numeric_columns


def check_column_query_mismatch(entities: dict, query: str, result: AmbiguityResult):
    """
    Detect when detected column doesn't appear in query text.

    This catches cases where fuzzy matching picked the wrong column.
    """
    column = entities.get("column")
    if not column:
        return

    query_lower = query.lower()

    # Check if column name appears in query
    if column.lower() not in query_lower:
        # Check confidence if available
        if "_confidence" in entities:
            col_conf = entities["_confidence"].get("column", 100)
            if col_conf < Config.CONFIDENCE_THRESHOLD_COLUMN:
                result.ambiguity_types.append("column_query_mismatch")


def calculate_overall_confidence(entities: dict) -> float:
    """
    Calculate composite confidence score.

    Returns a value between 0.0 and 1.0
    """
    if "_confidence" not in entities:
        return 0.5

    weights = {
        "table": 0.4,
        "column": 0.3,
    }

    scores = {
        "table": entities["_confidence"].get("table", 0) / 100,
        "column": entities["_confidence"].get("column", 100) / 100,
    }

    # Add bonus for having aggregation and where conditions
    if entities.get("aggregation"):
        scores["aggregation"] = 1.0
        weights["aggregation"] = 0.2
    else:
        scores["aggregation"] = 0.5
        weights["aggregation"] = 0.2

    if entities.get("where"):
        scores["where"] = 1.0
        weights["where"] = 0.1
    else:
        scores["where"] = 0.7
        weights["where"] = 0.1

    # Calculate weighted average
    return sum(scores[k] * weights[k] for k in weights)
