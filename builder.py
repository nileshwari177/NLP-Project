"""
Modular Advanced SQL Builder
Uses the sophisticated query processor with modular interface
"""

from typing import Dict
from interactive_query_processor import QueryProcessor as AdvancedProcessor


class ModularBuilder:
    """
    Modular wrapper around advanced query processor
    Each method builds ONE SQL clause
    """

    def __init__(self):
        """Initialize with advanced processor"""
        self.advanced = AdvancedProcessor()

    def build_all(self, data: Dict) -> str:
        """
        Main building pipeline - uses advanced processor
        Handles complex queries with proper SELECT logic, WHERE, JOIN, etc.
        """
        return self.advanced.process(data)

    # Individual builders for modular access
    def build_select(self, data: Dict) -> str:
        """Build SELECT clause"""
        return self.advanced._build_select(data)

    def build_from(self, data: Dict) -> str:
        """Build FROM clause"""
        return self.advanced._build_from(data)

    def build_where(self, data: Dict) -> str:
        """Build WHERE clause"""
        return self.advanced._build_where(data)

    def build_order(self, data: Dict) -> str:
        """Build ORDER BY clause"""
        return self.advanced._build_order(data)

    def build_limit(self, data: Dict) -> str:
        """Build LIMIT clause"""
        return self.advanced._build_limit(data)

    def explain(self, data: Dict, sql: str) -> str:
        """Generate human-readable explanation"""
        return self.advanced.explain_query(data, sql)


# Simple function-based API
def build(data: Dict) -> str:
    """
    Build SQL query from extracted data

    Args:
        data: Dictionary with extracted keywords

    Returns:
        SQL query string
    """
    builder = ModularBuilder()
    return builder.build_all(data)
