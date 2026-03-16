
"""
AI-Powered Disambiguator
Uses Claude API to resolve ambiguities in natural language queries interactively
"""

import anthropic
import json
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()


class AmbiguityDetector:
    """Detects ambiguities in extracted keywords"""

    # Confidence thresholds
    TABLE_CONFIDENCE_THRESHOLD = 65.0
    COLUMN_CONFIDENCE_THRESHOLD = 70.0
    FILTER_CONFIDENCE_THRESHOLD = 80.0

    @staticmethod
    def detect(keywords: Dict) -> Tuple[bool, List[str], Dict]:
        """
        Detect ambiguities in extracted keywords

        Returns:
            (is_ambiguous, issues_list, suggestions_dict)
        """
        issues = []
        suggestions = {}

        # Check 1: Low table confidence
        if keywords['table'] and keywords['table_confidence'] < AmbiguityDetector.TABLE_CONFIDENCE_THRESHOLD:
            issues.append("uncertain_table")
            suggestions['table_confidence'] = keywords['table_confidence']

        # Check 2: Missing or uncertain column
        if keywords['intent'] in ['aggregation', 'ranking']:
            if not keywords['primary_column']:
                issues.append("missing_column")
                suggestions['available_columns'] = keywords.get('all_mentioned_columns', [])
            elif keywords['column_confidence'] < AmbiguityDetector.COLUMN_CONFIDENCE_THRESHOLD:
                issues.append("uncertain_column")
                suggestions['column_confidence'] = keywords['column_confidence']

        # Check 3: Aggregation without clear column
        if keywords['aggregation'] and not keywords['primary_column']:
            issues.append("aggregation_without_column")
            if keywords['table']:
                from interactive_nlp_extractor import NLPExtractor
                extractor = NLPExtractor()
                suggestions['numeric_columns'] = extractor.get_numeric_columns(keywords['table'])

        # Check 4: Ranking without column (multiple numeric columns available)
        if keywords['ranking_direction'] and keywords['limit']:
            if not keywords['primary_column']:
                issues.append("ranking_without_column")
                if keywords['table']:
                    from interactive_nlp_extractor import NLPExtractor
                    extractor = NLPExtractor()
                    numeric_cols = extractor.get_numeric_columns(keywords['table'])
                    if len(numeric_cols) > 1:
                        suggestions['numeric_columns'] = numeric_cols

        # Check 5: Conflicting intent (only if we have aggregation NOT caused by highest/lowest)
        # Don't flag conflict if aggregation is MAX/MIN and we have ranking (common pattern: "top 10 highest")
        if keywords['aggregation'] and keywords['ranking_direction']:
            # Allow MAX with DESC or MIN with ASC (these are natural pairs)
            if not ((keywords['aggregation'] == 'MAX' and keywords['ranking_direction'] == 'DESC') or
                    (keywords['aggregation'] == 'MIN' and keywords['ranking_direction'] == 'ASC')):
                issues.append("conflicting_intent")

        is_ambiguous = len(issues) > 0

        return is_ambiguous, issues, suggestions


class AIDisambiguator:
    """Uses Claude API to resolve ambiguities through interactive conversation"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-haiku-20241022"  # Fast and efficient

    def generate_clarification_questions(
        self,
        original_query: str,
        keywords: Dict,
        issues: List[str],
        suggestions: Dict
    ) -> str:
        """
        Generate natural clarification questions using Claude

        Returns:
            String containing clarifying questions
        """
        # Build context for Claude
        context = self._build_context(original_query, keywords, issues, suggestions)

        prompt = f"""You are helping clarify an ambiguous database query. The user asked:
"{original_query}"

Context:
{context}

Generate a brief, friendly clarification question (1-2 sentences) to resolve the ambiguity.
Be conversational and helpful. Ask only about the most critical ambiguity.

Example good questions:
- "I found multiple numeric columns (cgpa, marks, year). Which one should I rank by?"
- "Should I calculate the average of 'marks' or 'cgpa'?"
- "Did you mean the 'students' table? I'm 70% confident."

Your question:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            question = message.content[0].text.strip()
            return question

        except Exception as e:
            # Fallback to simple question generation
            return self._fallback_question(issues, suggestions)

    def parse_clarification_response(
        self,
        user_response: str,
        keywords: Dict,
        issues: List[str],
        suggestions: Dict
    ) -> Dict:
        """
        Parse user's clarification response using Claude

        Returns:
            Dict with updated values for keywords
        """
        prompt = f"""The user was asked a clarification question about their database query.

Original query: "{keywords['original_query']}"
Current understanding: Table={keywords['table']}, Column={keywords['primary_column']}, Aggregation={keywords['aggregation']}

Issues: {', '.join(issues)}
Available options: {json.dumps(suggestions)}

User's response: "{user_response}"

Parse the user's response and extract what they want. Return a JSON object with updated values.
Only include fields that should be updated.

Example responses:
User: "cgpa" -> {{"primary_column": "cgpa"}}
User: "yes, students table" -> {{"table": "students"}}
User: "rank by marks" -> {{"primary_column": "marks"}}
User: "salary please" -> {{"primary_column": "salary"}}

Return ONLY valid JSON, nothing else:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                updates = json.loads(json_match.group())
                return updates
            else:
                return self._fallback_parse(user_response, suggestions)

        except Exception as e:
            return self._fallback_parse(user_response, suggestions)

    def _build_context(
        self,
        original_query: str,
        keywords: Dict,
        issues: List[str],
        suggestions: Dict
    ) -> str:
        """Build context string for Claude"""
        context_parts = []

        context_parts.append(f"Table detected: {keywords['table']} (confidence: {keywords['table_confidence']:.1f}%)")
        context_parts.append(f"Column detected: {keywords['primary_column']} (confidence: {keywords['column_confidence']:.1f}%)")

        if keywords['aggregation']:
            context_parts.append(f"Aggregation: {keywords['aggregation']}")

        if keywords['ranking_direction']:
            context_parts.append(f"Ranking: {keywords['ranking_direction']}, limit: {keywords['limit']}")

        if suggestions.get('numeric_columns'):
            context_parts.append(f"Available numeric columns: {', '.join(suggestions['numeric_columns'])}")

        context_parts.append(f"\nAmbiguity issues: {', '.join(issues)}")

        return '\n'.join(context_parts)

    def _fallback_question(self, issues: List[str], suggestions: Dict) -> str:
        """Generate simple fallback question when API fails"""
        if "missing_column" in issues or "ranking_without_column" in issues:
            cols = suggestions.get('numeric_columns', [])
            if cols:
                return f"Which column should I use? Available options: {', '.join(cols)}"

        if "uncertain_table" in issues:
            return "Did I detect the correct table? Please confirm."

        if "aggregation_without_column" in issues:
            cols = suggestions.get('numeric_columns', [])
            if cols:
                return f"Which column should I aggregate? Options: {', '.join(cols)}"

        return "I'm not sure I understood correctly. Can you clarify?"

    def _fallback_parse(self, user_response: str, suggestions: Dict) -> Dict:
        """Simple fallback parsing when API fails"""
        import re

        updates = {}
        response_lower = user_response.lower()

        # Check if user mentioned a column
        if 'numeric_columns' in suggestions:
            for col in suggestions['numeric_columns']:
                if col in response_lower:
                    updates['primary_column'] = col
                    break

        return updates

    def resolve_interactively(
        self,
        original_query: str,
        keywords: Dict,
        max_rounds: int = 2
    ) -> Dict:
        """
        Main interactive resolution loop

        Returns:
            Updated keywords dict
        """
        current_keywords = keywords.copy()

        for round_num in range(max_rounds):
            # Detect ambiguities
            is_ambiguous, issues, suggestions = AmbiguityDetector.detect(current_keywords)

            if not is_ambiguous:
                print("\n✓ Query understood clearly!")
                break

            # Generate clarification question
            question = self.generate_clarification_questions(
                original_query,
                current_keywords,
                issues,
                suggestions
            )

            print(f"\n🤔 {question}")

            # Get user response
            user_response = input("👉 Your answer: ").strip()

            if not user_response:
                print("Skipping clarification...")
                break

            # Parse response and update keywords
            updates = self.parse_clarification_response(
                user_response,
                current_keywords,
                issues,
                suggestions
            )

            # Apply updates
            for key, value in updates.items():
                current_keywords[key] = value
                print(f"   Updated {key} → {value}")

            # Re-assess confidence
            if 'primary_column' in updates:
                current_keywords['column_confidence'] = 100.0

        return current_keywords


# Import for fallback parsing
import re