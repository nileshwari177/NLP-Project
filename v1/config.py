import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for the NLP-to-SQL system."""

    CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLARIFICATION_ENABLED = os.getenv("CLARIFICATION_ENABLED", "true").lower() == "true"

    # Confidence thresholds for ambiguity detection
    CONFIDENCE_THRESHOLD_TABLE = 65.0
    CONFIDENCE_THRESHOLD_COLUMN = 70.0

    # Maximum number of clarification rounds per query
    MAX_CLARIFICATION_ROUNDS = 2

    # Context storage type: "memory" or "file"
    CONTEXT_STORAGE = "memory"


def validate_config():
    """Validate configuration at startup."""
    if Config.CLARIFICATION_ENABLED and not Config.CLAUDE_API_KEY:
        print("Warning: CLARIFICATION_ENABLED is true but ANTHROPIC_API_KEY is not set.")
        print("Clarification features will be disabled.")
        print("To enable: Set ANTHROPIC_API_KEY in your .env file or environment variables.")
        Config.CLARIFICATION_ENABLED = False

    return True
