"""
Interactive Query Processor
Converts extracted keywords into SQL queries
"""

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

        # Prioritize intent over raw aggregation presence
        if intent == 'ranking' and column:
            # For ranking, show ID and the ranking column
            return f"SELECT id, {column}"
        elif intent == 'aggregation' and aggregation and column:
            # Aggregation query (only when intent is actually aggregation)
            return f"SELECT {aggregation}({column}) as result"
        elif column:
            # Specific column
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

        if direction and column:
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
