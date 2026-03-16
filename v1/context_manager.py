from datetime import datetime
from schema_registry import SCHEMA


class QueryContext:
    """Stores context for a single query."""

    def __init__(self, query: str, entities: dict, ir: dict, sql: str):
        self.query = query
        self.entities = entities
        self.ir = ir
        self.sql = sql
        self.timestamp = datetime.now()


class ConversationContext:
    """Stores context for a conversation session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = []
        self.last_query = None
        self.last_entities = None
        self.last_sql = None
        self.created_at = datetime.now()

    def add_query(self, query_context: QueryContext):
        """Add a query to the session history."""
        self.history.append(query_context)
        self.last_query = query_context.query
        self.last_entities = query_context.entities
        self.last_sql = query_context.sql


class ContextManager:
    """Manages conversation contexts and follow-up detection."""

    def __init__(self, storage_type="memory"):
        self.storage_type = storage_type
        self.sessions = {}  # session_id -> ConversationContext

    def create_session(self, session_id: str) -> ConversationContext:
        """Create a new conversation session."""
        context = ConversationContext(session_id)
        self.sessions[session_id] = context
        return context

    def get_context(self, session_id: str) -> ConversationContext:
        """Retrieve session context, create if doesn't exist."""
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]

    def add_query(self, session_id: str, query_context: QueryContext):
        """Add query to session history."""
        context = self.get_context(session_id)
        context.add_query(query_context)

    def detect_followup(self, query: str, context: ConversationContext) -> dict:
        """
        Detect if query is a follow-up to previous conversation.

        Returns dict with:
        - is_followup: bool
        - type: str (modifier, addition, table_inference)
        - reference: str (last, all, etc.)
        """
        # If no history, can't be a follow-up
        if not context.history:
            return {"is_followup": False}

        query_lower = query.lower()

        # Pattern 1: Modifier words ("now", "also", "instead", "but")
        modifier_words = ["now", "also", "instead", "but", "rather"]
        if any(word in query_lower for word in modifier_words):
            return {
                "is_followup": True,
                "type": "modifier",
                "reference": "last"
            }

        # Pattern 2: Addition words ("add", "include", "with", "and")
        addition_phrases = ["add ", "include ", "with ", " and ", "also "]
        if any(phrase in query_lower for phrase in addition_phrases):
            return {
                "is_followup": True,
                "type": "addition",
                "reference": "last"
            }

        # Pattern 3: No table mentioned but has operations
        has_table = any(table.lower() in query_lower for table in SCHEMA.keys())
        has_alias = False
        for table_info in SCHEMA.values():
            if "aliases" in table_info:
                if any(alias.lower() in query_lower for alias in table_info["aliases"]):
                    has_table = True
                    break

        # Check for operation keywords
        operation_words = ["top", "bottom", "show", "list", "get", "find", "best", "worst"]
        has_operation = any(word in query_lower for word in operation_words)

        if not has_table and has_operation:
            return {
                "is_followup": True,
                "type": "table_inference",
                "reference": "last"
            }

        # Pattern 4: Direction change ("show bottom" after "show top")
        if context.last_entities:
            last_direction = context.last_entities.get("direction")
            if last_direction == "DESC" and any(word in query_lower for word in ["bottom", "worst", "lowest"]):
                return {
                    "is_followup": True,
                    "type": "direction_change",
                    "reference": "last"
                }
            elif last_direction == "ASC" and any(word in query_lower for word in ["top", "best", "highest"]):
                return {
                    "is_followup": True,
                    "type": "direction_change",
                    "reference": "last"
                }

        return {"is_followup": False}

    def merge_with_context(self, new_entities: dict, context: ConversationContext) -> dict:
        """
        Merge new entities with previous context.

        Returns merged entities dict.
        """
        if not context.last_entities:
            return new_entities

        last = context.last_entities.copy()
        merged = last.copy()

        # Override with non-null new values
        for key, value in new_entities.items():
            if key == "_confidence":
                # Always use new confidence scores
                merged["_confidence"] = value
            elif key == "where":
                # Append WHERE conditions if new ones exist
                if value:
                    merged["where"] = last.get("where", []) + value
            elif key == "direction":
                # Change direction if explicitly specified
                if value is not None:
                    merged["direction"] = value
            elif key == "limit":
                # Update limit if specified
                if value is not None:
                    merged["limit"] = value
            elif key == "table":
                # Use new table if specified, else keep old
                if value is not None:
                    merged["table"] = value
            elif key == "column":
                # Use new column if specified, else keep old
                if value is not None:
                    merged["column"] = value
            elif key == "aggregation":
                # Use new aggregation if specified, else keep old
                if value is not None:
                    merged["aggregation"] = value
            else:
                # For any other fields, use new value if not None
                if value is not None:
                    merged[key] = value

        return merged

    def clear_session(self, session_id: str):
        """Clear a session's history."""
        if session_id in self.sessions:
            del self.sessions[session_id]
