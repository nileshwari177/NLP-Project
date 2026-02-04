from schema_registry import SCHEMA


PRIORITY_METRICS = [
    "cgpa",
    "marks",
    "score",
    "rating",
    "price",
    "revenue",
    "units_sold"
]


def build_ir(parsed):
    table = parsed["table"]

    if not table:
        raise ValueError("Table not detected")

    columns = SCHEMA[table]["columns"]

    aggregation = parsed["aggregation"]
    direction = parsed["direction"]
    limit = parsed["limit"]
    where = parsed["where"]

    metric_column = None

    if direction:
        metric_column = choose_metric(columns)

    if aggregation:
        metric_column = choose_metric(columns)

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