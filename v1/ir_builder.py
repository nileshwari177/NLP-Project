from schema_registry import SCHEMA


PRIORITY_METRICS = [
    "cgpa",
    "marks",
    "score",
    "rating",
    "price",
    "revenue",
    "units_sold",
    "salary",
    "quantity",
    "year",
    "year_joined"
]


def build_ir(parsed):
    """Build intermediate representation with enhanced column detection."""
    table = parsed["table"]

    if not table:
        raise ValueError("Table not detected")

    if table not in SCHEMA:
        raise ValueError(f"Table '{table}' not found in schema")

    columns = SCHEMA[table]["columns"]

    aggregation = parsed["aggregation"]
    direction = parsed["direction"]
    limit = parsed["limit"]
    where = parsed["where"]
    detected_column = parsed.get("column")

    # Use detected column or choose metric from priority list
    metric_column = detected_column or (choose_metric(columns) if (direction or aggregation) else None)

    ir = {
        "select": ["*"],
        "aggregation": aggregation,
        "table": table,
        "where": where,
        "order_by": None,
        "limit": limit
    }

    if metric_column and direction:
        ir["order_by"] = {
            "column": metric_column,
            "direction": direction
        }

    if aggregation and metric_column:
        ir["select"] = [metric_column]

    return ir


def choose_metric(columns):
    for metric in PRIORITY_METRICS:
        if metric in columns:
            return metric
    return None