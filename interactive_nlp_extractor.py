"""
Enhanced NLP Keyword Extractor
Extracts keywords, entities, and intent from natural language queries
"""

from rapidfuzz import process, fuzz
import re
from typing import Dict, List, Tuple, Optional

class NLPExtractor:
    """Enhanced NLP extraction with multi-strategy keyword detection"""

    # Database schema definition
    SCHEMA = {
        "students": {
            "columns": ["id", "name", "cgpa", "marks", "year"],
            "numeric_columns": ["cgpa", "marks", "year"],
            "aliases": ["student", "pupils", "learners", "scholars"]
        },
        "cars": {
            "columns": ["id", "car_name", "price", "units_sold", "year"],
            "numeric_columns": ["price", "units_sold", "year"],
            "aliases": ["car", "vehicles", "automobiles", "autos"]
        },
        "employees": {
            "columns": ["id", "name", "salary", "department", "year_joined", "rating"],
            "numeric_columns": ["salary", "year_joined", "rating"],
            "aliases": ["employee", "staff", "workers", "personnel"]
        },
        "products": {
            "columns": ["id", "product_name", "price", "quantity", "category", "rating"],
            "numeric_columns": ["price", "quantity", "rating"],
            "aliases": ["product", "items", "goods", "merchandise"]
        }
    }

    # Intent keywords
    RANKING_KEYWORDS = {
        "top": ("DESC", ["highest", "best", "top", "maximum", "largest", "greatest", "most"]),
        "bottom": ("ASC", ["lowest", "worst", "bottom", "minimum", "smallest", "least", "fewest"])
    }

    AGGREGATION_KEYWORDS = {
        "AVG": ["average", "avg", "mean"],
        "SUM": ["total", "sum", "add up", "combined"],
        "COUNT": ["count", "number of", "how many", "total number"],
        "MAX": ["maximum", "max", "highest", "largest", "greatest"],
        "MIN": ["minimum", "min", "lowest", "smallest", "least"]
    }

    COMPARISON_OPERATORS = {
        ">": ["greater than", "more than", "above", "over", "exceeds", "higher than"],
        "<": ["less than", "below", "under", "fewer than", "lower than"],
        ">=": ["at least", "minimum of", "no less than", "or more"],
        "<=": ["at most", "maximum of", "no more than", "or less"],
        "=": ["equals", "equal to", "is", "exactly"],
        "!=": ["not equal to", "not", "different from"]
    }

    # Column synonyms for better matching
    COLUMN_SYNONYMS = {
        "cgpa": ["gpa", "grade point", "grade", "grades"],
        "marks": ["score", "scores", "points", "mark", "test score"],
        "name": ["student name", "employee name", "staff name", "worker name"],
        "car_name": ["vehicle", "car", "automobile", "car model"],
        "product_name": ["product", "item", "item name"],
        "salary": ["wage", "wages", "pay", "income", "compensation"],
        "price": ["cost", "costing", "value", "amount", "pricing"],
        "units_sold": ["sales", "sold", "units", "quantity sold"],
        "quantity": ["stock", "available", "in stock", "qty"],
        "rating": ["rate", "rated", "score", "review score"],
        "department": ["dept", "division", "section"],
        "category": ["type", "kind", "class"]
    }

    def __init__(self):
        """Initialize the NLP extractor"""
        self.reverse_synonyms = self._build_reverse_synonyms()

    def _build_reverse_synonyms(self) -> Dict[str, str]:
        """Build reverse mapping from synonyms to canonical column names"""
        reverse = {}
        for canonical, synonyms in self.COLUMN_SYNONYMS.items():
            reverse[canonical] = canonical
            for synonym in synonyms:
                reverse[synonym] = canonical
        return reverse

    def extract_keywords(self, query: str) -> Dict:
        """
        Main extraction method - extracts all keywords and entities from query

        Returns:
            Dict with table, columns, aggregation, filters, ranking, etc.
        """
        query_lower = query.lower()

        # Extract all components
        table_info = self._extract_table(query_lower)
        columns_info = self._extract_columns(query_lower, table_info['table'])
        aggregation_info = self._extract_aggregation(query_lower)
        ranking_info = self._extract_ranking(query_lower)
        filters_info = self._extract_filters(query_lower, table_info['table'])

        # Build comprehensive result
        result = {
            "table": table_info['table'],
            "table_confidence": table_info['confidence'],
            "primary_column": columns_info['primary'],
            "column_confidence": columns_info['confidence'],
            "all_mentioned_columns": columns_info['all_columns'],
            "aggregation": aggregation_info['function'],
            "aggregation_confidence": aggregation_info['confidence'],
            "ranking_direction": ranking_info['direction'],
            "limit": ranking_info['limit'],
            "filters": filters_info['conditions'],
            "filter_confidence": filters_info['confidence'],
            "intent": self._determine_intent(aggregation_info, ranking_info, filters_info),
            "original_query": query
        }

        return result

    def _extract_table(self, query: str) -> Dict:
        """Extract table name with fuzzy matching"""
        all_table_names = []
        for table_name, info in self.SCHEMA.items():
            all_table_names.append(table_name)
            all_table_names.extend(info['aliases'])

        # Try exact word matching first
        words = query.split()
        for word in words:
            if word in all_table_names:
                canonical = self._get_canonical_table_name(word)
                return {"table": canonical, "confidence": 100.0}

        # Fuzzy matching fallback
        result = process.extractOne(
            query,
            all_table_names,
            scorer=fuzz.partial_ratio,
            score_cutoff=60.0
        )

        if result:
            matched_name, confidence, _ = result
            canonical = self._get_canonical_table_name(matched_name)
            return {"table": canonical, "confidence": float(confidence)}

        return {"table": None, "confidence": 0.0}

    def _get_canonical_table_name(self, name: str) -> Optional[str]:
        """Get canonical table name from alias"""
        for table_name, info in self.SCHEMA.items():
            if name == table_name or name in info['aliases']:
                return table_name
        return None

    def _extract_columns(self, query: str, table: Optional[str]) -> Dict:
        """Extract columns mentioned in query with multi-strategy detection"""
        if not table or table not in self.SCHEMA:
            return {"primary": None, "confidence": 0.0, "all_columns": []}

        available_columns = self.SCHEMA[table]['columns']
        detected_columns = []
        max_confidence = 0.0
        primary_column = None

        # Strategy 1: Exact word boundary matching
        for col in available_columns:
            pattern = r'\b' + re.escape(col) + r'\b'
            if re.search(pattern, query):
                detected_columns.append(col)
                if not primary_column:
                    primary_column = col
                    max_confidence = 100.0

        # Strategy 2: Synonym matching
        words = query.split()
        for word in words:
            if word in self.reverse_synonyms:
                canonical_col = self.reverse_synonyms[word]
                if canonical_col in available_columns and canonical_col not in detected_columns:
                    detected_columns.append(canonical_col)
                    if not primary_column:
                        primary_column = canonical_col
                        max_confidence = 95.0

        # Strategy 3: Aggregation context (e.g., "average marks", "total salary")
        for agg_func, keywords in self.AGGREGATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    for col in self.SCHEMA[table]['numeric_columns']:
                        if col in query or any(syn in query for syn in self.COLUMN_SYNONYMS.get(col, [])):
                            if col not in detected_columns:
                                detected_columns.append(col)
                            # Prefer this column as primary if it appears near the aggregation keyword
                            if not primary_column or primary_column not in self.SCHEMA[table]['numeric_columns']:
                                primary_column = col
                                max_confidence = 90.0

        # Strategy 4: Fuzzy matching as last resort
        if not primary_column:
            result = process.extractOne(
                query,
                available_columns,
                scorer=fuzz.partial_ratio,
                score_cutoff=70.0
            )
            if result:
                col, confidence, _ = result
                primary_column = col
                max_confidence = float(confidence)
                if col not in detected_columns:
                    detected_columns.append(col)

        return {
            "primary": primary_column,
            "confidence": max_confidence,
            "all_columns": detected_columns
        }

    def _extract_aggregation(self, query: str) -> Dict:
        """Extract aggregation function if present"""
        for agg_func, keywords in self.AGGREGATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return {"function": agg_func, "confidence": 95.0}

        return {"function": None, "confidence": 0.0}

    def _extract_ranking(self, query: str) -> Dict:
        """Extract ranking direction and limit"""
        direction = None
        limit = None

        # Check for ranking keywords
        for rank_type, (rank_dir, keywords) in self.RANKING_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    direction = rank_dir
                    break
            if direction:
                break

        # Extract limit number
        limit_patterns = [
            r'top\s+(\d+)',
            r'bottom\s+(\d+)',
            r'first\s+(\d+)',
            r'last\s+(\d+)',
            r'show\s+(\d+)',
            r'get\s+(\d+)',
            r'(\d+)\s+(?:students|cars|employees|products)'
        ]

        for pattern in limit_patterns:
            match = re.search(pattern, query)
            if match:
                limit = int(match.group(1))
                break

        return {"direction": direction, "limit": limit}

    def _extract_filters(self, query: str, table: Optional[str]) -> Dict:
        """Extract WHERE conditions and filters"""
        conditions = []
        confidence = 0.0

        if not table or table not in self.SCHEMA:
            return {"conditions": conditions, "confidence": confidence}

        # Extract comparison filters (e.g., "salary > 50000")
        for operator, keywords in self.COMPARISON_OPERATORS.items():
            for keyword in keywords:
                pattern = rf'(\w+)\s+{re.escape(keyword)}\s+([0-9.]+)'
                match = re.search(pattern, query)
                if match:
                    column = match.group(1)
                    value = match.group(2)

                    # Normalize column name
                    if column in self.reverse_synonyms:
                        column = self.reverse_synonyms[column]

                    if column in self.SCHEMA[table]['columns']:
                        conditions.append({
                            "column": column,
                            "operator": operator,
                            "value": value,
                            "type": "comparison"
                        })
                        confidence = 90.0

        # Extract BETWEEN filters
        between_pattern = r'(\w+)\s+between\s+([0-9.]+)\s+and\s+([0-9.]+)'
        match = re.search(between_pattern, query)
        if match:
            column = match.group(1)
            value1 = match.group(2)
            value2 = match.group(3)

            if column in self.reverse_synonyms:
                column = self.reverse_synonyms[column]

            if column in self.SCHEMA[table]['columns']:
                conditions.append({
                    "column": column,
                    "operator": "BETWEEN",
                    "value": [value1, value2],
                    "type": "range"
                })
                confidence = 95.0

        # Extract string equality filters (e.g., "department = Engineering")
        dept_pattern = r'(?:in|from|of)\s+(?:department|dept|division)\s+(\w+)'
        match = re.search(dept_pattern, query)
        if match and "department" in self.SCHEMA[table]['columns']:
            conditions.append({
                "column": "department",
                "operator": "=",
                "value": match.group(1),
                "type": "string"
            })
            confidence = 85.0

        # Extract category filters
        cat_pattern = r'(?:in|from|of)\s+(?:category|type)\s+(\w+)'
        match = re.search(cat_pattern, query)
        if match and "category" in self.SCHEMA[table]['columns']:
            conditions.append({
                "column": "category",
                "operator": "=",
                "value": match.group(1),
                "type": "string"
            })
            confidence = 85.0

        # Extract year filters
        year_pattern = r'(?:in|from|for)\s+(?:year|the year)\s+(\d{4})'
        match = re.search(year_pattern, query)
        if match:
            year_col = "year" if "year" in self.SCHEMA[table]['columns'] else "year_joined"
            if year_col in self.SCHEMA[table]['columns']:
                conditions.append({
                    "column": year_col,
                    "operator": "=",
                    "value": match.group(1),
                    "type": "year"
                })
                confidence = 90.0

        return {"conditions": conditions, "confidence": confidence}

    def _determine_intent(self, agg_info: Dict, rank_info: Dict, filter_info: Dict) -> str:
        """Determine the primary intent of the query"""
        # If we have ranking direction AND limit, prioritize ranking over aggregation
        if rank_info['direction'] and rank_info['limit']:
            return "ranking"
        elif agg_info['function']:
            return "aggregation"
        elif filter_info['conditions']:
            return "filtering"
        else:
            return "retrieval"

    def get_numeric_columns(self, table: str) -> List[str]:
        """Get list of numeric columns for a table"""
        if table in self.SCHEMA:
            return self.SCHEMA[table]['numeric_columns']
        return []

    def validate_column(self, table: str, column: str) -> bool:
        """Check if column exists in table"""
        if table in self.SCHEMA:
            return column in self.SCHEMA[table]['columns']
        return False