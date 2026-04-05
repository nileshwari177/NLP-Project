"""
Interactive Query Processor
Converts extracted keywords into SQL queries
"""

import re
from typing import Dict, List, Optional


class QueryProcessor:
    """Processes keywords and generates SQL queries"""

    def __init__(self):
        """Initialize query processor"""
        pass

    def process(self, keywords: Dict) -> str:
        """
        Main processing method - converts keywords to SQL

        Args:
            keywords: Dict containing extracted keywords and entities

        Returns:
            SQL query string
        """
        # Validate we have minimum required info
        if not keywords.get('table'):
            raise ValueError("Cannot generate query: no table detected")

        # Build SQL components
        select_clause = self._build_select(keywords)
        from_clause = self._build_from(keywords)
        where_clause = self._build_where(keywords)
        order_clause = self._build_order(keywords)
        limit_clause = self._build_limit(keywords)

        # Assemble query
        sql_parts = [select_clause, from_clause]

        if where_clause:
            sql_parts.append(where_clause)

        if order_clause:
            sql_parts.append(order_clause)

        if limit_clause:
            sql_parts.append(limit_clause)

        sql = ' '.join(sql_parts) + ';'

        return sql

    def _build_select(self, keywords: Dict) -> str:
        """Build SELECT clause"""
        table = keywords['table']
        column = keywords.get('primary_column')
        aggregation = keywords.get('aggregation')
        intent = keywords.get('intent')
        original_query = keywords.get('original_query', '').lower()

        # Handle calculations first
        if intent == 'calculation' and keywords.get('has_calculation'):
            calculation_expr = keywords.get('calculation')
            if calculation_expr:
                return f"SELECT {calculation_expr} as result"

        # Prioritize intent over raw aggregation presence
        if intent == 'ranking' and column:
            # For ranking, show ID and the ranking column
            return f"SELECT id, {column}"
        elif intent == 'aggregation' and aggregation:
            # For COUNT aggregations, use COUNT(id) unless specific column requested
            if aggregation == 'COUNT':
                # Check if query explicitly asks for counting a specific thing
                if column and any(word in original_query for word in [f'count {column}', f'how many {column}']):
                    return f"SELECT {aggregation}({column}) as result"
                else:
                    # Default to COUNT(id)
                    return f"SELECT COUNT(id) as result"
            elif column:
                # Other aggregations (AVG, SUM, MAX, MIN) use the column
                return f"SELECT {aggregation}({column}) as result"
            else:
                # Aggregation without column (shouldn't happen, but handle it)
                return "SELECT *"
        elif intent in ['filtering', 'retrieval']:
            # For filtering or basic retrieval, use SELECT * unless specific column requested
            # Key distinction:
            # - "show all students" / "get all employees" -> SELECT *
            # - "get employee names" / "show product names" -> SELECT name/product_name

            # Check if query has "all" keyword - if so, always use SELECT *
            if 'all' in original_query.split()[:4]:  # Check first 4 words
                return "SELECT *"

            # Check if query explicitly asks for specific columns
            column_request_words = ['get', 'show', 'display', 'list']
            has_explicit_column = False

            # Check if the query explicitly asks for a specific column name
            if column and not keywords.get('filters'):
                # Skip if query explicitly says "all"
                if f'all {table}' in original_query or f'{table}' == original_query.split()[-1]:
                    # "show all students" or "students" at the end -> SELECT *
                    return "SELECT *"

                # Remove underscores for matching (e.g., "product_name" -> "product name")
                column_no_underscore = column.replace('_', ' ')

                for word in column_request_words:
                    # Check for column name or plural form anywhere after the action word
                    # E.g., "get employee names", "show product name"
                    column_words = column_no_underscore.split()
                    for col_word in column_words:
                        # Match singular or plural form
                        # Pattern allows words in between: "get ... name" or "get ... names"
                        if re.search(f'{word}.+{col_word}s?\\b', original_query):
                            has_explicit_column = True
                            break
                    if has_explicit_column:
                        break

            if has_explicit_column:
                # Explicit column request without filters (e.g., "Get employee names")
                return f"SELECT {column}"
            else:
                # Default to SELECT * for filtering and retrieval
                return "SELECT *"
        elif column:
            # Fallback: specific column
            return f"SELECT {column}"
        else:
            # All columns
            return "SELECT *"

    def _build_from(self, keywords: Dict) -> str:
        """Build FROM clause"""
        return f"FROM {keywords['table']}"

    def _build_where(self, keywords: Dict) -> str:
        """Build WHERE clause from filters"""
        filters = keywords.get('filters', [])

        if not filters:
            return ""

        conditions = []

        for filter_item in filters:
            column = filter_item['column']
            operator = filter_item['operator']
            value = filter_item['value']
            filter_type = filter_item.get('type', 'comparison')

            if operator == 'BETWEEN':
                # Range condition
                val1, val2 = value
                conditions.append(f"{column} BETWEEN {val1} AND {val2}")
            elif operator in ['IN', 'NOT IN']:
                # IN operator with multiple values
                if isinstance(value, list):
                    if filter_type == 'string' or filter_type == 'year':
                        values_str = ', '.join([f"'{v}'" for v in value])
                    else:
                        values_str = ', '.join([str(v) for v in value])
                    conditions.append(f"{column} {operator} ({values_str})")
                else:
                    # Single value
                    if filter_type == 'string':
                        conditions.append(f"{column} {operator} ('{value}')")
                    else:
                        conditions.append(f"{column} {operator} ({value})")
            elif operator == 'LIKE' or filter_type == 'like':
                # LIKE operator for pattern matching
                conditions.append(f"{column} LIKE '{value}'")
            elif filter_type == 'string' or filter_type == 'year':
                # String comparison (need quotes)
                conditions.append(f"{column} {operator} '{value}'")
            else:
                # Numeric comparison
                conditions.append(f"{column} {operator} {value}")

        if conditions:
            return "WHERE " + " AND ".join(conditions)

        return ""

    def _build_order(self, keywords: Dict) -> str:
        """Build ORDER BY clause"""
        direction = keywords.get('ranking_direction')
        column = keywords.get('primary_column')
        intent = keywords.get('intent')

        # Only add ORDER BY for ranking queries, not for aggregations
        # Aggregations like MAX/MIN don't need ORDER BY
        if direction and column and intent == 'ranking':
            return f"ORDER BY {column} {direction}"

        return ""

    def _build_limit(self, keywords: Dict) -> str:
        """Build LIMIT clause"""
        limit = keywords.get('limit')

        if limit:
            return f"LIMIT {limit}"

        return ""

    def explain_query(self, keywords: Dict, sql: str) -> str:
        """
        Generate a human-readable explanation of what the query does

        Args:
            keywords: Extracted keywords
            sql: Generated SQL query

        Returns:
            Human-readable explanation
        """
        explanation_parts = []

        # Start with intent
        intent = keywords.get('intent', 'retrieval')

        if intent == 'aggregation':
            agg = keywords['aggregation']
            col = keywords['primary_column']
            table = keywords['table']
            explanation_parts.append(f"Calculate the {agg.lower()} of {col} from the {table} table")

        elif intent == 'ranking':
            direction_word = "highest" if keywords['ranking_direction'] == 'DESC' else "lowest"
            limit = keywords['limit']
            col = keywords['primary_column']
            table = keywords['table']
            explanation_parts.append(f"Find the top {limit} {table} with the {direction_word} {col}")

        elif intent == 'filtering':
            table = keywords['table']
            explanation_parts.append(f"Filter {table} records")

        else:
            table = keywords['table']
            col = keywords.get('primary_column', 'all columns')
            explanation_parts.append(f"Retrieve {col} from {table}")

        # Add filter details
        filters = keywords.get('filters', [])
        if filters:
            filter_descs = []
            for f in filters:
                col = f['column']
                op = f['operator']
                val = f['value']

                if op == 'BETWEEN':
                    filter_descs.append(f"{col} between {val[0]} and {val[1]}")
                elif op == '=':
                    filter_descs.append(f"{col} equals {val}")
                elif op == '>':
                    filter_descs.append(f"{col} greater than {val}")
                elif op == '<':
                    filter_descs.append(f"{col} less than {val}")
                elif op == '>=':
                    filter_descs.append(f"{col} at least {val}")
                elif op == '<=':
                    filter_descs.append(f"{col} at most {val}")
                else:
                    filter_descs.append(f"{col} {op} {val}")

            explanation_parts.append("where " + ", and ".join(filter_descs))

        return " ".join(explanation_parts) + "."

    def suggest_improvements(self, keywords: Dict) -> List[str]:
        """
        Suggest potential improvements or additional filters

        Returns:
            List of suggestion strings
        """
        suggestions = []

        # Check if query could benefit from additional filters
        if not keywords.get('filters'):
            if keywords['table'] in ['students', 'employees', 'products', 'cars']:
                suggestions.append("💡 You could add filters like 'where year = 2024' to narrow results")

        # Check if aggregation without grouping
        if keywords.get('aggregation') and not keywords.get('filters'):
            suggestions.append("💡 Consider adding conditions to filter which records to aggregate")

        # Check if ranking without filters
        if keywords.get('ranking_direction') and keywords.get('limit'):
            if not keywords.get('filters'):
                suggestions.append("💡 You could filter by year or category before ranking")

        return suggestions
