import anthropic
import json
import time
from schema_registry import SCHEMA
from ambiguity_detector import AmbiguityResult


class ClarificationManager:
    """Manages the clarification workflow using Claude API."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required for ClarificationManager")

        self.client = anthropic.Anthropic(api_key=api_key)
        # Using Claude 3 Haiku - fast, efficient, widely available
        self.model = "claude-3-haiku-20240307"

    def generate_clarifying_questions(
        self,
        query: str,
        entities: dict,
        ambiguity_result: AmbiguityResult
    ) -> list[str]:
        """
        Generate natural clarifying questions using Claude API.

        Returns a list of natural language questions to ask the user.
        """
        # Build schema context
        schema_context = self._build_schema_context(entities.get("table"))

        # Build alternatives context
        alternatives_text = self._format_alternatives(ambiguity_result.alternatives)

        prompt = f"""You are a clarification assistant for a natural language to SQL converter.

The user asked: "{query}"

We detected these entities:
- Table: {entities.get('table')}
- Column: {entities.get('column')}
- Aggregation: {entities.get('aggregation')}
- Direction: {entities.get('direction')}
- Limit: {entities.get('limit')}

{schema_context}

Detected ambiguities: {', '.join(ambiguity_result.ambiguity_types)}

{alternatives_text}

Your task: Generate 1-2 specific, natural questions to resolve these ambiguities.
- Be concise and specific
- Provide clear options when available
- Focus on: ranking criteria and filters (NOT output format)
- Each question should be a single clear sentence

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{"type": "ranking_column", "text": "What should we rank the cars by?", "options": ["price", "units_sold", "year"]}},
    {{"type": "filter", "text": "Any year range or filters to apply?", "options": null}}
  ]
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

        try:
            response = self._call_claude_with_retry(prompt)
            result = json.loads(response)
            questions = result.get("questions", [])

            # Extract just the text from questions
            return [q["text"] for q in questions if "text" in q]

        except Exception as e:
            print(f"Error generating questions: {e}")
            # Fallback to simple questions
            return self._generate_fallback_questions(ambiguity_result)

    def parse_user_response(
        self,
        user_response: str,
        questions: list[str],
        entities: dict
    ) -> dict:
        """
        Parse user's clarification response using Claude API.

        Returns a dict of updates to apply to entities.
        """
        prompt = f"""Parse the user's clarification response for an SQL query.

Original entities:
{json.dumps({k: v for k, v in entities.items() if k != "_confidence"}, indent=2)}

Questions asked:
{json.dumps(questions, indent=2)}

User's response: "{user_response}"

Your task: Extract structured updates from the user's response.

Return ONLY valid JSON in this exact format:
{{
  "updates": {{
    "column": "price",
    "where": [{{"column": "year", "operator": ">", "value": "2020"}}],
    "direction": "DESC"
  }}
}}

Rules:
- Only include fields that need updating based on the user's response
- For column names, use exact column names from the schema
- For WHERE conditions, use proper SQL operators (>, <, =, etc.)
- If no updates needed, return: {{"updates": {{}}}}

IMPORTANT: Return ONLY the JSON object, no other text."""

        try:
            response = self._call_claude_with_retry(prompt)
            result = json.loads(response)
            return result.get("updates", {})

        except Exception as e:
            print(f"Error parsing response: {e}")
            # Fallback to simple parsing
            return self._simple_parse_response(user_response, entities)

    def update_entities(self, entities: dict, parsed_response: dict) -> dict:
        """
        Apply clarification updates to entities dict.

        Returns updated entities dict.
        """
        updated = entities.copy()

        for key, value in parsed_response.items():
            if key == "where" and value:
                # Append WHERE conditions
                existing_where = updated.get("where", [])
                updated["where"] = existing_where + value
            elif value is not None:
                # Update other fields
                updated[key] = value

        return updated

    def _build_schema_context(self, table: str) -> str:
        """Build context about available schema columns."""
        if not table or table not in SCHEMA:
            return "Schema: Not available"

        columns = SCHEMA[table]["columns"]
        col_list = ", ".join([f"{col} ({col_type})" for col, col_type in columns.items()])

        return f"Available columns in '{table}': {col_list}"

    def _format_alternatives(self, alternatives: dict) -> str:
        """Format alternatives into readable text."""
        if not alternatives:
            return "No alternatives available."

        lines = []
        for key, value in alternatives.items():
            if isinstance(value, list):
                lines.append(f"Possible {key}s: {', '.join(value)}")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def _call_claude_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call Claude API with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )

                return response.content[0].text

            except anthropic.APIError as e:
                if attempt == max_retries - 1:
                    raise
                print(f"API error, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # Exponential backoff

    def _generate_fallback_questions(self, ambiguity_result: AmbiguityResult) -> list[str]:
        """Generate simple fallback questions when Claude API fails."""
        questions = []

        if "missing_ranking_column" in ambiguity_result.ambiguity_types:
            options = ambiguity_result.alternatives.get("column", [])
            if options:
                questions.append(f"What should we rank by? Options: {', '.join(options)}")

        if "aggregation_without_column" in ambiguity_result.ambiguity_types:
            options = ambiguity_result.alternatives.get("column", [])
            if options:
                questions.append(f"Which column should we aggregate? Options: {', '.join(options)}")

        if "low_table_confidence" in ambiguity_result.ambiguity_types:
            questions.append("Please confirm the table name.")

        return questions if questions else ["Please clarify your query."]

    def _simple_parse_response(self, user_response: str, entities: dict) -> dict:
        """Simple fallback parser when Claude API fails."""
        updates = {}

        response_lower = user_response.lower()

        # Try to extract column name
        table = entities.get("table")
        if table and table in SCHEMA:
            for col in SCHEMA[table]["columns"].keys():
                if col.lower() in response_lower:
                    updates["column"] = col
                    break

        return updates
