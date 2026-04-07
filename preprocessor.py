"""
NLTK Preprocessor
Lemmatization and synonym matching for better query understanding
"""

import re
from typing import Dict, Set
try:
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import wordnet
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


# Synonym mapping for SQL-related terms
SYNONYMS = {
    # Table synonyms
    'student': ['pupil', 'learner'],
    'employee': ['worker', 'staff', 'personnel'],
    'product': ['item', 'goods', 'merchandise'],
    'customer': ['client', 'buyer', 'consumer'],
    'order': ['purchase', 'transaction'],
    'car': ['vehicle', 'automobile'],

    # Column synonyms
    'name': ['title', 'label'],
    'price': ['cost', 'rate', 'amount'],
    'salary': ['wage', 'pay', 'compensation'],
    'email': ['mail', 'e-mail'],
    'year': ['yr'],
    'quantity': ['qty', 'amount', 'count'],

    # Aggregation synonyms
    'average': ['mean', 'avg'],
    'total': ['sum', 'aggregate'],
    'count': ['number', 'tally'],
    'maximum': ['max', 'highest', 'largest'],
    'minimum': ['min', 'lowest', 'smallest'],

    # Ranking synonyms
    'top': ['best', 'highest'],
    'bottom': ['worst', 'lowest'],

    # Filter synonyms
    'greater': ['more', 'above', 'over'],
    'less': ['fewer', 'below', 'under'],
    'equal': ['same', 'equals'],
}


class Preprocessor:
    """NLTK-based preprocessor for query enhancement"""

    def __init__(self):
        """Initialize preprocessor with NLTK lemmatizer"""
        self.lemmatizer = None

        if NLTK_AVAILABLE:
            try:
                self.lemmatizer = WordNetLemmatizer()
                # Try to use wordnet, download if needed
                try:
                    wordnet.synsets('test')
                except:
                    print("Downloading NLTK data (one-time setup)...")
                    nltk.download('wordnet', quiet=True)
                    nltk.download('omw-1.4', quiet=True)
            except:
                pass

    def lemmatize(self, query: str) -> str:
        """
        Lemmatize words in query
        Example: "students" → "student", but preserve SQL keywords
        """
        if not self.lemmatizer:
            return query

        # SQL keywords to preserve
        preserve = {
            'count', 'average', 'avg', 'sum', 'total', 'max', 'min',
            'top', 'bottom', 'highest', 'lowest', 'like', 'between',
            'greater', 'less', 'equal', 'and', 'or', 'not', 'in',
            'plus', 'minus', 'times', 'divide', 'orders', 'order',
            'rating', 'status', 'discount', 'bonus', 'number', 'spent', 'budget'  # Common keywords
        }

        words = query.split()
        lemmatized = []

        for word in words:
            # Keep numbers and special characters as-is
            if word.isdigit() or not word.isalpha():
                lemmatized.append(word)
            # Preserve SQL keywords
            elif word.lower() in preserve:
                lemmatized.append(word.lower())
            else:
                # Try noun first, then verb
                lemma = self.lemmatizer.lemmatize(word.lower(), pos='n')
                if lemma == word.lower():
                    lemma = self.lemmatizer.lemmatize(word.lower(), pos='v')
                lemmatized.append(lemma)

        return ' '.join(lemmatized)

    def expand_synonyms(self, query: str) -> str:
        """
        Replace synonyms with canonical forms
        Example: "pupils" → "students", "wage" → "salary"
        BUT preserve SQL keywords like count, average, sum, etc.
        """
        query_lower = query.lower()

        # SQL keywords to preserve
        sql_keywords = {
            'count', 'average', 'avg', 'sum', 'total', 'max', 'min',
            'top', 'bottom', 'highest', 'lowest', 'like', 'between',
            'greater', 'less', 'equal', 'and', 'or', 'not', 'in',
            'plus', 'minus', 'times', 'divide', 'number', 'rating', 'status',
            'discount', 'bonus', 'spent', 'budget'
        }

        # Build reverse mapping (synonym → canonical)
        reverse_map = {}
        for canonical, synonyms in SYNONYMS.items():
            for syn in synonyms:
                reverse_map[syn] = canonical

        # Replace synonyms
        words = query_lower.split()
        result = []

        for word in words:
            # Preserve SQL keywords
            if word in sql_keywords:
                result.append(word)
                continue

            # First lemmatize if available
            if self.lemmatizer:
                lemma = self.lemmatizer.lemmatize(word, pos='n')
                if lemma in reverse_map:
                    result.append(reverse_map[lemma])
                elif word in reverse_map:
                    result.append(reverse_map[word])
                else:
                    result.append(word)
            else:
                # Just use synonym mapping
                if word in reverse_map:
                    result.append(reverse_map[word])
                else:
                    result.append(word)

        return ' '.join(result)

    def normalize_numbers(self, query: str) -> str:
        """
        Normalize number representations
        Example: "fifty" → "50", "1st" → "1"
        """
        number_words = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10',
            'twenty': '20', 'thirty': '30', 'fifty': '50', 'hundred': '100'
        }

        words = query.lower().split()
        result = []

        for word in words:
            # Convert number words
            if word in number_words:
                result.append(number_words[word])
            # Remove ordinal suffixes (1st, 2nd, 3rd, etc.)
            elif re.match(r'\d+(st|nd|rd|th)', word):
                result.append(re.sub(r'(st|nd|rd|th)$', '', word))
            else:
                result.append(word)

        return ' '.join(result)

    def preprocess(self, query: str, verbose: bool = False) -> str:
        """
        Full preprocessing pipeline
        1. Lemmatize
        2. Expand synonyms
        3. Normalize numbers
        """
        original = query

        # Step 1: Lemmatize
        query = self.lemmatize(query)

        # Step 2: Expand synonyms
        query = self.expand_synonyms(query)

        # Step 3: Normalize numbers
        query = self.normalize_numbers(query)

        if verbose and query != original.lower():
            print(f"Preprocessing: '{original}' → '{query}'")

        return query

    def get_wordnet_synonyms(self, word: str) -> Set[str]:
        """
        Get synonyms from WordNet
        Example: "student" → {"pupil", "scholar", "learner"}
        """
        if not NLTK_AVAILABLE:
            return set()

        synonyms = set()

        try:
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    # Add lemma name (replacing underscores)
                    synonyms.add(lemma.name().replace('_', ' ').lower())
        except:
            pass

        return synonyms


# Global preprocessor instance
_preprocessor = Preprocessor()


def preprocess(query: str, verbose: bool = False) -> str:
    """
    Preprocess query with lemmatization and synonym matching

    Args:
        query: Natural language query
        verbose: Show preprocessing steps

    Returns:
        Preprocessed query
    """
    return _preprocessor.preprocess(query, verbose)


def get_synonyms(word: str) -> Set[str]:
    """Get all synonyms for a word (WordNet + custom)"""
    # Custom synonyms
    custom = set(SYNONYMS.get(word.lower(), []))

    # WordNet synonyms
    wordnet_syns = _preprocessor.get_wordnet_synonyms(word.lower())

    return custom | wordnet_syns
