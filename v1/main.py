from extractor import extract_entities
from ir_builder import build_ir
from compiler import compile_mysql
from ambiguity_detector import detect_ambiguities
from clarification_manager import ClarificationManager
from context_manager import ContextManager, QueryContext
from config import Config, validate_config
import uuid


def run():
    """Enhanced main loop with clarification support."""
    print("English to SQL (Interactive Mode)")
    print("Commands: 'exit' to quit, 'new' to start new session\n")

    # Validate configuration
    validate_config()

    # Initialize managers
    context_mgr = ContextManager(storage_type=Config.CONTEXT_STORAGE)
    clarify_mgr = None

    if Config.CLARIFICATION_ENABLED:
        try:
            clarify_mgr = ClarificationManager(Config.CLAUDE_API_KEY)
        except Exception as e:
            print(f"Warning: Could not initialize clarification manager: {e}")
            print("Continuing without clarification features.\n")
            Config.CLARIFICATION_ENABLED = False

    # Create initial session
    session_id = str(uuid.uuid4())[:8]
    context_mgr.create_session(session_id)
    print(f"Session: {session_id}\n")

    while True:
        query = input(">> ")

        if query.lower() == "exit":
            print("Goodbye!")
            break

        elif query.lower() == "new":
            session_id = str(uuid.uuid4())[:8]
            context_mgr.create_session(session_id)
            print(f"New session: {session_id}\n")
            continue

        elif not query.strip():
            continue

        try:
            # Get conversation context
            context = context_mgr.get_context(session_id)

            # Check if this is a follow-up query
            followup_info = context_mgr.detect_followup(query, context)

            # Extract entities from query
            entities = extract_entities(query)

            # Merge with context if follow-up
            if followup_info["is_followup"]:
                entities = context_mgr.merge_with_context(entities, context)
                print(f"[Follow-up detected: {followup_info['type']}]")

            # Detect ambiguities
            if Config.CLARIFICATION_ENABLED and clarify_mgr:
                ambiguity_result = detect_ambiguities(entities, query)

                if ambiguity_result.is_ambiguous:
                    print("\n[Clarification needed]")

                    try:
                        # Generate clarifying questions
                        questions = clarify_mgr.generate_clarifying_questions(
                            query, entities, ambiguity_result
                        )

                        # Ask user
                        for i, q in enumerate(questions, 1):
                            print(f"{i}. {q}")

                        user_response = input("Your answer: ")

                        # Parse response and update entities
                        parsed = clarify_mgr.parse_user_response(
                            user_response, questions, entities
                        )
                        entities = clarify_mgr.update_entities(entities, parsed)
                        print("[Clarification applied]\n")

                    except Exception as e:
                        print(f"Clarification error: {e}")
                        print("Proceeding with original detection...\n")

            # Build IR and compile to SQL
            ir = build_ir(entities)
            sql = compile_mysql(ir)

            # Display result
            print("\nGenerated SQL:")
            print(sql)
            print()

            # Save to context
            query_ctx = QueryContext(
                query=query,
                entities=entities,
                ir=ir,
                sql=sql
            )
            context_mgr.add_query(session_id, query_ctx)

        except ValueError as e:
            print(f"Error: {e}\n")

        except Exception as e:
            print(f"Unexpected error: {e}\n")


if __name__ == "__main__":
    run()
