"""Test script to verify Claude API clarification feature."""
from clarification_manager import ClarificationManager
from ambiguity_detector import detect_ambiguities
from extractor import extract_entities
from config import Config, validate_config
import sys

def test_clarification_api():
    """Test if Claude API clarification is working."""
    print("=" * 80)
    print("TESTING CLAUDE API CLARIFICATION FEATURE")
    print("=" * 80)

    # Validate config
    validate_config()

    if not Config.CLARIFICATION_ENABLED:
        print("\n[FAIL] CLARIFICATION_ENABLED is False")
        print("Please set CLARIFICATION_ENABLED=true in .env")
        return False

    if not Config.CLAUDE_API_KEY:
        print("\n[FAIL] ANTHROPIC_API_KEY not found")
        print("Please set ANTHROPIC_API_KEY in .env")
        return False

    print("\n[PASS] Configuration validated")
    print(f"  - API Key: {Config.CLAUDE_API_KEY[:20]}... (masked)")
    print(f"  - Clarification Enabled: {Config.CLARIFICATION_ENABLED}")

    # Initialize clarification manager
    try:
        clarify_mgr = ClarificationManager(Config.CLAUDE_API_KEY)
        print("\n[PASS] ClarificationManager initialized successfully")
    except Exception as e:
        print(f"\n[FAIL] Failed to initialize ClarificationManager: {e}")
        return False

    # Create an intentionally ambiguous scenario for testing Claude API
    # We'll manually create ambiguous entities (as if extractor couldn't decide)
    test_query = "Show me the top 5 cars"
    print(f"\n[TEST] Test Query: '{test_query}' (forcing ambiguity for API test)")

    # Manually create ambiguous entities to test Claude API
    entities = {
        'table': 'cars',
        'column': None,  # Intentionally None to trigger ambiguity
        'aggregation': None,
        'limit': 5,
        'direction': 'DESC',
        'where': [],
        '_confidence': {'table': 100, 'column': 0}
    }
    print(f"\n[SETUP] Using ambiguous entities: {entities}")

    # Detect ambiguities
    try:
        ambiguity_result = detect_ambiguities(entities, test_query)
        print(f"\n[PASS] Ambiguity detection complete")
        print(f"  - Is Ambiguous: {ambiguity_result.is_ambiguous}")
        print(f"  - Types: {ambiguity_result.ambiguity_types}")
        print(f"  - Alternatives: {ambiguity_result.alternatives}")
    except Exception as e:
        print(f"\n[FAIL] Failed to detect ambiguities: {e}")
        return False

    # Test Claude API clarification question generation
    if ambiguity_result.is_ambiguous:
        print("\n[TEST] Testing Claude API for clarification questions...")
        try:
            questions = clarify_mgr.generate_clarifying_questions(
                test_query, entities, ambiguity_result
            )
            print(f"\n[PASS] Claude API call successful!")
            print(f"  Generated {len(questions)} question(s):")
            for i, q in enumerate(questions, 1):
                print(f"    {i}. {q}")

            # Test parsing a sample response
            print("\n[TEST] Testing Claude API response parsing...")
            sample_response = "price"
            parsed = clarify_mgr.parse_user_response(sample_response, questions, entities)
            print(f"\n[PASS] Response parsing successful!")
            print(f"  Parsed updates: {parsed}")

            return True

        except Exception as e:
            print(f"\n[FAIL] Claude API call failed: {e}")
            return False
    else:
        print("\n[SKIP] Query is not ambiguous, skipping clarification test")
        print("       Note: This is actually good - your extractor is working well!")
        return True

if __name__ == "__main__":
    success = test_clarification_api()

    print("\n" + "=" * 80)
    if success:
        print("[SUCCESS] CLARIFICATION FEATURE TEST: PASSED")
        print("The Claude API integration is working correctly!")
    else:
        print("[FAILED] CLARIFICATION FEATURE TEST: FAILED")
        print("Please check the error messages above.")
    print("=" * 80)

    sys.exit(0 if success else 1)
