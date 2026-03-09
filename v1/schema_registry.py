SCHEMA = {
    "students": {
        "columns": {
            "id": "integer",
            "name": "string",
            "cgpa": "float",
            "marks": "integer",
            "year": "integer"
        },
        "aliases": ["student", "pupils", "learners"]
    },
    "cars": {
        "columns": {
            "id": "integer",
            "car_name": "string",
            "price": "float",
            "units_sold": "integer",
            "year": "integer"
        },
        "aliases": ["car", "vehicles", "automobiles"]
    },
    "employees": {
        "columns": {
            "id": "integer",
            "name": "string",
            "salary": "float",
            "department": "string",
            "year_joined": "integer",
            "rating": "float"
        },
        "aliases": ["employee", "staff", "workers"]
    },
    "products": {
        "columns": {
            "id": "integer",
            "product_name": "string",
            "price": "float",
            "quantity": "integer",
            "category": "string",
            "rating": "float"
        },
        "aliases": ["product", "items", "goods"]
    }
}

# Column type validation rules
COLUMN_TYPES = {
    "integer": {"validation": "int", "sql_type": "INT"},
    "float": {"validation": "float", "sql_type": "FLOAT"},
    "string": {"validation": "str", "sql_type": "VARCHAR(255)"}
}


def get_all_tables():
    """Get all table names including aliases."""
    all_tables = []
    for table, info in SCHEMA.items():
        all_tables.append(table)
        if "aliases" in info:
            all_tables.extend(info["aliases"])
    return all_tables


def get_canonical_table_name(table_or_alias):
    """Convert table alias to canonical table name."""
    for table, info in SCHEMA.items():
        if table == table_or_alias:
            return table
        if "aliases" in info and table_or_alias in info["aliases"]:
            return table
    return None