"""
Modular Advanced Extractor
Combines modular architecture with powerful features:
- RapidFuzz for fuzzy matching
- AI Disambiguator for unclear queries
- Multi-strategy extraction
- Synonym expansion
"""

from typing import Dict, List, Optional
from interactive_nlp_extractor import NLPExtractor as AdvancedExtractor
from preprocessor import preprocess


class ModularExtractor:
    """
    Modular wrapper around advanced extractor
    Each method extracts ONE piece of information using powerful techniques
    """

    def __init__(self, use_ai: bool = True, use_preprocessing: bool = True):
        """
        Initialize with powerful features

        Args:
            use_ai: Enable AI disambiguator for unclear queries
            use_preprocessing: Enable NLTK preprocessing
        """
        self.advanced = AdvancedExtractor()
        self.use_ai = use_ai
        self.use_preprocessing = use_preprocessing

    def preprocess_query(self, query: str) -> str:
        """Step 1: Preprocess query with NLTK"""
        if self.use_preprocessing:
            return preprocess(query, verbose=False)
        return query.lower()

    def extract_all(self, query: str) -> Dict:
        """
        Main extraction pipeline - uses advanced extractor
        Returns all extracted information in one shot
        """
        # Preprocess
        processed_query = self.preprocess_query(query)

        # Use advanced extractor with BOTH original and preprocessed queries
        # Original query preserves case for filter values (IT, HR, etc.)
        # Preprocessed query helps with table/column matching
        result = self.advanced.extract_keywords(processed_query, original_query=query)

        # Add original query
        result['original_query'] = query
        result['preprocessed_query'] = processed_query

        return result

    # Individual extractors for modular access
    def extract_table(self, data: Dict) -> str:
        """Extract table name"""
        return data.get('table')

    def extract_columns(self, data: Dict) -> List[str]:
        """Extract columns"""
        cols = []
        if data.get('primary_column'):
            cols.append(data['primary_column'])
        if data.get('calculation_columns'):
            cols.extend(data['calculation_columns'])
        return cols

    def extract_intent(self, data: Dict) -> str:
        """Extract query intent"""
        return data.get('intent', 'retrieval')

    def extract_aggregation(self, data: Dict) -> Optional[str]:
        """Extract aggregation function"""
        return data.get('aggregation')

    def extract_filters(self, data: Dict) -> List[Dict]:
        """Extract filter conditions"""
        return data.get('filters', [])

    def extract_calculation(self, data: Dict) -> Optional[str]:
        """Extract calculation expression"""
        if data.get('has_calculation'):
            return data.get('calculation')
        return None

    def extract_ranking(self, data: Dict) -> Optional[Dict]:
        """Extract ranking information"""
        if data.get('ranking_direction'):
            return {
                'direction': data['ranking_direction'],
                'limit': data.get('limit'),
                'column': data.get('primary_column')
            }
        return None

    def extract_limit(self, data: Dict) -> Optional[int]:
        """Extract limit value"""
        return data.get('limit')

    def extract_logical_operator(self, data: Dict) -> str:
        """Extract logical operator (AND/OR)"""
        return data.get('logical_operator', 'AND')


# Simple function-based API
def extract(query: str, use_ai: bool = True, use_preprocessing: bool = True) -> Dict:
    """
    Extract keywords from query using advanced techniques

    Args:
        query: Natural language query
        use_ai: Enable AI disambiguator
        use_preprocessing: Enable NLTK preprocessing

    Returns:
        Dictionary with all extracted information
    """
    extractor = ModularExtractor(use_ai=use_ai, use_preprocessing=use_preprocessing)
    return extractor.extract_all(query)
