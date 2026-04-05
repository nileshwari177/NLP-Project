"""
Interactive NLP-to-SQL with AI Clarification
Type your queries and get SQL - AI will ask you to clarify ambiguous queries!
"""

from extractor import extract
from builder import build
from ai_disambiguator import AmbiguityDetector, AIDisambiguator
from interactive_nlp_extractor import NLPExtractor
import os


def process_query_with_clarification(query: str):
    """Process query and ask for clarification if needed"""

    # Step 1: Extract keywords
    print("\n[Extracting keywords...]")
    keywords = extract(query, use_ai=False, use_preprocessing=True)

    # Step 2: Check for ambiguities (need schema for suggestions)
    extractor = NLPExtractor()
    schema = extractor.SCHEMA
    is_ambiguous, issues, suggestions = AmbiguityDetector.detect(keywords, schema)

    if not is_ambiguous:
        # Clear query - generate SQL directly
        print("[Query is clear - generating SQL...]")
        sql = build(keywords)
        return sql

    # Step 3: Query is ambiguous - ask for clarification
    print("\n[Query is ambiguous - AI will ask for clarification...]")

    # Check if AI is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠ AI requires ANTHROPIC_API_KEY environment variable.")
        print("Generating SQL with best guess...\n")
        sql = build(keywords)
        return sql

    try:
        # Initialize AI
        ai = AIDisambiguator()

        # Generate clarification question
        question = ai.generate_clarification_questions(
            query, keywords, issues, suggestions
        )

        # Ask user
        print(f"\n🤖 AI: {question}")
        user_response = input("You: ").strip()

        if not user_response:
            print("\n[No response - using best guess...]")
            sql = build(keywords)
            return sql

        # Parse user's clarification
        print("\n[Processing your clarification...]")
        updates = ai.parse_clarification_response(
            user_response, keywords, suggestions, issues
        )

        # Update keywords with clarification
        keywords.update(updates)

        # Handle special flags
        if updates.get('clear_aggregation'):
            keywords.pop('aggregation', None)  # Remove aggregation key if present

        # Generate SQL with updated keywords
        print("[Generating SQL with clarified intent...]")
        sql = build(keywords)
        return sql

    except Exception as e:
        print(f"\n⚠ AI error: {e}")
        print("Generating SQL with best guess...\n")
        sql = build(keywords)
        return sql


def main():
    print("=" * 80)
    print("INTERACTIVE NLP-TO-SQL WITH AI CLARIFICATION")
    print("=" * 80)
    print("\nType your natural language queries below.")
    print("AI will ask you clarifying questions for ambiguous queries!")
    print("\nType 'quit' or 'exit' to stop.\n")
    print("Try these:")
    print("  CONFIDENT:")
    print("    - Top 10 students with highest CGPA")
    print("    - Average salary of employees in IT department")
    print("    - students with name like John")
    print("\n  AMBIGUOUS (AI will ask for clarification):")
    print("    - show high performing students")
    print("    - top students")
    print("    - average of employees")
    print("\n" + "=" * 80 + "\n")

    while True:
        try:
            # Get user input
            query = input("Query: ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            # Process query with AI clarification
            sql = process_query_with_clarification(query)

            print(f"\n✓ Generated SQL:")
            print(f"  {sql}\n")
            print("-" * 80 + "\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}\n")
            print("-" * 80 + "\n")


if __name__ == "__main__":
    main()
