import anthropic
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class AmbiguityDetector:
    """Detects missing or low-confidence information in extracted keywords."""

    TABLE_THRESHOLD = 85.0  # Higher = more strict (triggers AI more)
    COLUMN_THRESHOLD = 85.0

    @staticmethod
    def detect(keywords: Dict, schema: Dict) -> Tuple[bool, List[str], Dict]:
        """
        Triggers AI when table/column/intent are missing or unclear.
        Returns: (is_ambiguous, issues_list, suggestions_dict)
        """
        issues = []
        suggestions = {}
        table = keywords.get('table')
        intent = keywords.get('intent')
        primary_col = keywords.get('primary_column')
        query_lower = keywords.get('original_query', '').lower()

        # ============================================================
        # 1. TABLE NOT IDENTIFIED - Ask user to specify table
        # ============================================================
        if not table or table == '':
            issues.append("no_table_identified")
            suggestions['all_tables'] = list(schema.keys())
            suggestions['message'] = "Please specify which table you want to query"

        # 2. TABLE IDENTIFIED BUT LOW CONFIDENCE
        elif keywords.get('table_confidence', 0) < AmbiguityDetector.TABLE_THRESHOLD:
            issues.append("uncertain_table")
            suggestions['detected_table'] = table
            suggestions['table_confidence'] = keywords.get('table_confidence')
            suggestions['all_tables'] = list(schema.keys())

        # ============================================================
        # 3. COLUMN NOT IDENTIFIED - Ask user to specify column
        # ============================================================
        needs_column = intent in ['aggregation', 'ranking', 'calculation']

        if needs_column and (not primary_col or primary_col == ''):
            issues.append("no_column_identified")
            if table and table in schema:
                suggestions['numeric_columns'] = schema[table].get('numeric_columns', [])
                suggestions['all_columns'] = schema[table].get('columns', [])
                suggestions['message'] = f"Please specify which column to use for {intent}"

        # 4. COLUMN IDENTIFIED BUT LOW CONFIDENCE
        elif primary_col and keywords.get('column_confidence', 0) < AmbiguityDetector.COLUMN_THRESHOLD:
            issues.append("uncertain_column")
            suggestions['detected_column'] = primary_col
            suggestions['column_confidence'] = keywords.get('column_confidence')
            if table and table in schema:
                suggestions['numeric_columns'] = schema[table].get('numeric_columns', [])

        # ============================================================
        # 5. INTENT DETECTION - Check for vague terms and correct intent
        # ============================================================

        # Check for vague terms that indicate ranking, not aggregation
        # "high performing" = rank by DESC
        # "low price" = rank by ASC
        vague_ranking_terms_desc = ['high', 'best', 'good', 'great', 'top', 'highest', 'performing', 'excellent']
        vague_ranking_terms_asc = ['low', 'worst', 'bad', 'poor', 'bottom', 'lowest', 'cheap']

        has_vague_desc = any(term in query_lower for term in vague_ranking_terms_desc)
        has_vague_asc = any(term in query_lower for term in vague_ranking_terms_asc)

        # If query has vague ranking terms, it's likely a ranking query
        if has_vague_desc or has_vague_asc:
            # Correct the intent if it was wrongly detected as aggregation
            if intent == 'aggregation' and not any(w in query_lower for w in ['average', 'avg', 'total', 'sum', 'count', 'maximum', 'minimum']):
                # This is actually a ranking query, not aggregation
                issues.append("wrong_intent_detected")
                suggestions['correct_intent'] = 'ranking'
                suggestions['ranking_direction'] = 'DESC' if has_vague_desc else 'ASC'
                suggestions['limit'] = 10  # Default limit for "high performing" queries

                if not primary_col:
                    issues.append("no_column_for_ranking")
                    if table and table in schema:
                        suggestions['numeric_columns'] = schema[table].get('numeric_columns', [])
                        suggestions['message'] = f"Which column defines '{query_lower}'? (e.g., for 'high performing', which metric?)"

        # Check if intent is still unclear
        if not intent or intent == 'retrieval':
            # Check if query has keywords suggesting specific intent
            has_ranking_keywords = any(w in query_lower for w in ['top', 'bottom', 'highest', 'lowest', 'best', 'worst', 'first', 'last'])
            has_agg_keywords = any(w in query_lower for w in ['average', 'avg', 'total', 'sum', 'count', 'how many', 'maximum', 'minimum', 'max', 'min'])

            if has_ranking_keywords and not keywords.get('ranking_direction'):
                issues.append("unclear_ranking_intent")
                suggestions['possible_intent'] = 'ranking'
                suggestions['message'] = "Do you want to rank/sort the results?"

            elif has_agg_keywords and not keywords.get('aggregation'):
                issues.append("unclear_aggregation_intent")
                suggestions['possible_intent'] = 'aggregation'
                suggestions['message'] = "Do you want to calculate an aggregate (average, sum, count, etc.)?"

        # ============================================================
        # 6. MULTIPLE INTERPRETATIONS POSSIBLE
        # ============================================================

        # Multiple numeric columns available for ranking/aggregation
        if needs_column and table and table in schema:
            numeric_cols = schema[table].get('numeric_columns', [])
            if len(numeric_cols) > 1 and not primary_col:
                issues.append("multiple_column_options")
                suggestions['numeric_columns'] = numeric_cols

        # Conflicting intent (aggregation + ranking)
        if keywords.get('aggregation') and keywords.get('ranking_direction'):
            is_max_desc = keywords['aggregation'] == 'MAX' and keywords['ranking_direction'] == 'DESC'
            is_min_asc = keywords['aggregation'] == 'MIN' and keywords['ranking_direction'] == 'ASC'
            if not (is_max_desc or is_min_asc):
                issues.append("conflicting_intent")
                suggestions['detected_aggregation'] = keywords['aggregation']
                suggestions['detected_ranking'] = keywords['ranking_direction']

        return len(issues) > 0, issues, suggestions


class AIDisambiguator:
    """Uses LLM to resolve query ambiguities via chat."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY missing")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-haiku-20241022"

    def generate_clarification_questions(self, query: str, keywords: Dict, issues: List[str], suggestions: Dict) -> str:
        """Generates a natural language question to ask the user based on what's missing."""

        # Priority-based question generation

        # 0. Wrong intent detected (e.g., "high performing" detected as aggregation instead of ranking)
        if "wrong_intent_detected" in issues or "no_column_for_ranking" in issues:
            cols = suggestions.get('numeric_columns', [])
            ranking_dir = suggestions.get('ranking_direction', 'DESC')
            query_hint = "highest" if ranking_dir == 'DESC' else "lowest"
            if cols:
                col_list = ', '.join(cols)
                return f"I think you want to rank by {query_hint} value. Which column? Available: {col_list}"
            return f"Which column should I rank by ({query_hint} first)?"

        # 1. No table identified
        if "no_table_identified" in issues:
            tables = suggestions.get('all_tables', [])
            if tables:
                table_list = ', '.join(tables[:5])  # Show first 5 tables
                return f"I couldn't identify which table to query. Available tables: {table_list}. Which table do you want?"
            return "Which table do you want to query?"

        # 2. Uncertain table
        if "uncertain_table" in issues:
            detected = suggestions.get('detected_table')
            confidence = suggestions.get('table_confidence', 0)
            return f"Did you mean the '{detected}' table? I'm {confidence:.0f}% confident. Please confirm or specify another table."

        # 3. No column identified
        if "no_column_identified" in issues:
            cols = suggestions.get('numeric_columns', [])
            intent = keywords.get('intent', 'operation')
            if cols:
                col_list = ', '.join(cols)
                return f"Which column should I use for {intent}? Available numeric columns: {col_list}"
            return f"Which column should I use for {intent}?"

        # 4. Uncertain column
        if "uncertain_column" in issues:
            detected = suggestions.get('detected_column')
            confidence = suggestions.get('column_confidence', 0)
            cols = suggestions.get('numeric_columns', [])
            col_list = ', '.join(cols) if cols else "see schema"
            return f"Did you mean column '{detected}'? I'm {confidence:.0f}% confident. Other options: {col_list}"

        # 5. Unclear ranking intent
        if "unclear_ranking_intent" in issues:
            return "Do you want to rank/sort the results (e.g., top 10, highest, lowest)? If yes, by which column?"

        # 6. Unclear aggregation intent
        if "unclear_aggregation_intent" in issues:
            return "Do you want to calculate an aggregate like average, sum, count, max, or min? If yes, of which column?"

        # 7. Vague terms
        if "vague_terms_in_query" in issues:
            return "Your query contains vague terms like 'high' or 'good'. Can you be more specific? (e.g., 'students with CGPA > 3.5')"

        # 8. Multiple column options
        if "multiple_column_options" in issues:
            cols = suggestions.get('numeric_columns', [])
            col_list = ', '.join(cols)
            return f"Multiple numeric columns available: {col_list}. Which one should I use?"

        # 9. Conflicting intent
        if "conflicting_intent" in issues:
            agg = suggestions.get('detected_aggregation')
            rank = suggestions.get('detected_ranking')
            return f"Your query seems to want both {agg} aggregation and {rank} ranking. Which do you prefer?"

        # Fallback: Use AI to generate question
        prompt = f"""User query: "{query}"
Detected: Table={keywords.get('table')}, Column={keywords.get('primary_column')}, Intent={keywords.get('intent')}
Issues: {', '.join(issues)}
Options: {json.dumps(suggestions)}

Generate ONE short (1-2 sentences) helpful question to clarify what's missing or unclear."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            return "Please clarify: which table and column do you want to query?"

    def parse_clarification_response(self, user_response: str, keywords: Dict, suggestions: Dict, issues: List[str]) -> Dict:
        """Parses user input to update keyword dictionary."""
        updates = {}
        response_lower = user_response.lower().strip()

        # Simple rule-based parsing for common responses
        # 1. User specifying a table name
        if "no_table_identified" in issues or "uncertain_table" in issues:
            available_tables = suggestions.get('all_tables', [])
            for table in available_tables:
                if table.lower() in response_lower:
                    updates['table'] = table
                    updates['table_confidence'] = 100.0
                    break

        # 2. User specifying a column name for RANKING (e.g., "high performing students")
        if "wrong_intent_detected" in issues or "no_column_for_ranking" in issues:
            available_columns = suggestions.get('numeric_columns', []) + suggestions.get('all_columns', [])
            for col in available_columns:
                if col.lower() in response_lower:
                    # Correct the intent to ranking
                    updates['intent'] = 'ranking'
                    updates['primary_column'] = col
                    updates['column_confidence'] = 100.0
                    updates['ranking_direction'] = suggestions.get('ranking_direction', 'DESC')
                    updates['limit'] = suggestions.get('limit', 10)
                    # Clear wrong aggregation
                    updates['aggregation'] = ''
                    updates['clear_aggregation'] = True  # Flag to remove aggregation key
                    break

        # 3. User specifying a column name for other intents
        if "no_column_identified" in issues or "uncertain_column" in issues or "multiple_column_options" in issues:
            available_columns = suggestions.get('numeric_columns', []) + suggestions.get('all_columns', [])
            for col in available_columns:
                if col.lower() in response_lower:
                    updates['primary_column'] = col
                    updates['column_confidence'] = 100.0
                    break

        # 4. User confirming intent
        if "unclear_ranking_intent" in issues:
            if any(w in response_lower for w in ['yes', 'rank', 'sort', 'top', 'highest', 'lowest']):
                updates['intent'] = 'ranking'
                # Try to extract column for ranking
                available_columns = suggestions.get('numeric_columns', [])
                for col in available_columns:
                    if col.lower() in response_lower:
                        updates['primary_column'] = col
                        updates['column_confidence'] = 100.0
                        break

        if "unclear_aggregation_intent" in issues:
            agg_map = {
                'average': 'AVG', 'avg': 'AVG', 'mean': 'AVG',
                'sum': 'SUM', 'total': 'SUM',
                'count': 'COUNT', 'number': 'COUNT', 'how many': 'COUNT',
                'maximum': 'MAX', 'max': 'MAX', 'highest': 'MAX',
                'minimum': 'MIN', 'min': 'MIN', 'lowest': 'MIN'
            }
            for keyword, agg_func in agg_map.items():
                if keyword in response_lower:
                    updates['intent'] = 'aggregation'
                    updates['aggregation'] = agg_func
                    break
            # Try to extract column for aggregation
            available_columns = suggestions.get('numeric_columns', [])
            for col in available_columns:
                if col.lower() in response_lower:
                    updates['primary_column'] = col
                    updates['column_confidence'] = 100.0
                    break

        # 4. If simple parsing didn't work, use AI
        if not updates:
            prompt = f"""Original Query: "{keywords.get('original_query')}"
Current Understanding: Table={keywords.get('table')}, Column={keywords.get('primary_column')}, Intent={keywords.get('intent')}
Available Options: {json.dumps(suggestions)}
Issues: {', '.join(issues)}

User's clarification: "{user_response}"

Parse the user's response and return ONLY a JSON object with the fields to update.
Examples:
- User says "students" -> {{"table": "students"}}
- User says "cgpa" -> {{"primary_column": "cgpa"}}
- User says "yes, rank by salary" -> {{"intent": "ranking", "primary_column": "salary"}}
- User says "average of marks" -> {{"intent": "aggregation", "aggregation": "AVG", "primary_column": "marks"}}

Return ONLY valid JSON, nothing else:"""

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=150,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text.strip()
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    ai_updates = json.loads(match.group())
                    updates.update(ai_updates)
            except Exception as e:
                pass  # Return empty updates if AI fails

        return updates