def compile_mysql(ir):
    table = ir["table"]
    aggregation = ir["aggregation"]
    where = ir["where"]
    order_by = ir["order_by"]
    limit = ir["limit"]
    select_columns = ir["select"]

    # SELECT clause
    if aggregation:
        select_clause = f"SELECT {aggregation}({select_columns[0]})"
    else:
        select_clause = "SELECT *"

    # FROM clause
    from_clause = f"FROM {table}"

    # WHERE clause
    where_clause = ""
    if where:
        conditions = []
        for condition in where:
            operator = condition['operator']
            column = condition['column']
            value = condition['value']

            # Handle BETWEEN operator specially (value is a tuple)
            if operator == "BETWEEN":
                conditions.append(
                    f"{column} BETWEEN {value[0]} AND {value[1]}"
                )
            else:
                conditions.append(
                    f"{column} {operator} {value}"
                )
        where_clause = "WHERE " + " AND ".join(conditions)

    # ORDER BY clause
    order_clause = ""
    if order_by:
        order_clause = f"ORDER BY {order_by['column']} {order_by['direction']}"

    # LIMIT clause
    limit_clause = ""
    if limit:
        limit_clause = f"LIMIT {limit}"

    query = " ".join(
        part for part in [
            select_clause,
            from_clause,
            where_clause,
            order_clause,
            limit_clause
        ] if part
    )

    return query + ";"