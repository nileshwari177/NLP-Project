#!/usr/bin/env python3
"""
Interactive NLP to SQL Application
Main entry point for the interactive query system

Usage:
    python interactive_app.py

Features:
    - Natural language query input
    - NLP-powered keyword extraction
    - AI-powered ambiguity resolution using Claude
    - Interactive clarification prompts
    - SQL query generation
    - Human-readable query explanations
"""

import os
import sys
from dotenv import load_dotenv
from typing import Optional

# Import our modules
from interactive_nlp_extractor import NLPExtractor
from ai_disambiguator import AIDisambiguator, AmbiguityDetector
from interactive_query_processor import QueryProcessor
from typing import Dict, List, Tuple
# Load environment variables
load_dotenv()


class InteractiveNLPApp:
    """Main interactive application"""

    def __init__(self):
        """Initialize the application"""
        self.extractor = NLPExtractor()
        self.processor = QueryProcessor()
        self.disambiguator = None

        # Check for API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                self.disambiguator = AIDisambiguator(api_key)
                self.ai_enabled = True
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize AI disambiguator: {e}")
                print("   Continuing without AI-powered clarification...")
                self.ai_enabled = False
        else:
            print("⚠️  Warning: ANTHROPIC_API_KEY not found in environment")
            print("   AI-powered clarification will be disabled.")
            print("   Set your API key in .env file to enable this feature.\n")
            self.ai_enabled = False

    def print_banner(self):
        """Print welcome banner"""
        print("=" * 70)
        print("🤖  INTERACTIVE NLP TO SQL CONVERTER")
        print("=" * 70)
        print()
        print("Convert natural language queries to SQL using NLP and AI!")
        print()
        print("Features:")
        print("  ✓ Natural language understanding")
        print("  ✓ Smart keyword extraction")
        if self.ai_enabled:
            print("  ✓ AI-powered ambiguity resolution (Claude)")
        print("  ✓ Interactive clarification")
        print("  ✓ SQL query generation")
        print()
        print("Available tables: students, cars, employees, products")
        print()
        print("Commands:")
        print("  'exit' or 'quit' - Exit the application")
        print("  'help' - Show example queries")
        print("  'tables' - Show available tables and columns")
        print()
        print("=" * 70)
        print()

    def print_help(self):
        """Print example queries"""
        print("\n📚 EXAMPLE QUERIES:\n")

        examples = [
            ("Basic retrieval", [
                "Show all students",
                "Get employee names",
                "List all cars"
            ]),
            ("Aggregation", [
                "What is the average marks of students?",
                "Calculate total salary of employees",
                "Count how many products are available"
            ]),
            ("Ranking/Top-N", [
                "Show top 10 students with highest CGPA",
                "Get bottom 5 cars with lowest price",
                "Find 3 employees with highest salary"
            ]),
            ("Filtering", [
                "Find students with marks greater than 80",
                "Show cars with price between 20000 and 50000",
                "Get employees in department Engineering"
            ]),
            ("Complex queries", [
                "Top 5 students with highest marks in year 2024",
                "Average salary of employees in IT department",
                "Products with rating above 4.5 in category Electronics"
            ])
        ]

        for category, queries in examples:
            print(f"  {category}:")
            for query in queries:
                print(f"    • {query}")
            print()

    def print_tables(self):
        """Print available tables and their columns"""
        print("\n📊 AVAILABLE TABLES:\n")

        for table_name, info in self.extractor.SCHEMA.items():
            print(f"  {table_name}:")
            print(f"    Columns: {', '.join(info['columns'])}")
            print(f"    Numeric columns: {', '.join(info['numeric_columns'])}")
            print(f"    Aliases: {', '.join(info['aliases'])}")
            print()

    def process_query(self, query: str) -> Optional[str]:
        """
        Process a single query through the full pipeline

        Args:
            query: Natural language query

        Returns:
            Generated SQL query or None if failed
        """
        print(f"\n📝 Processing: \"{query}\"\n")

        # Step 1: Extract keywords using NLP
        print("🔍 Extracting keywords...")
        keywords = self.extractor.extract_keywords(query)

        # Show what was detected
        print(f"   Table: {keywords['table']} ({keywords['table_confidence']:.1f}% confidence)")
        print(f"   Column: {keywords['primary_column']} ({keywords['column_confidence']:.1f}% confidence)")
        if keywords['aggregation']:
            print(f"   Aggregation: {keywords['aggregation']}")
        if keywords['ranking_direction']:
            print(f"   Ranking: {keywords['ranking_direction']} (limit: {keywords['limit']})")
        if keywords['filters']:
            print(f"   Filters: {len(keywords['filters'])} condition(s)")
        print(f"   Intent: {keywords['intent']}")

        # Step 2: Check for ambiguities
        print("\n🔎 Checking for ambiguities...")
        is_ambiguous, issues, suggestions = AmbiguityDetector.detect(keywords)

        if is_ambiguous:
            print(f"   Found {len(issues)} ambiguity issue(s): {', '.join(issues)}")

            # Step 3: Resolve ambiguities interactively if AI is enabled
            if self.ai_enabled and self.disambiguator:
                print("\n💬 Starting interactive clarification...")
                keywords = self.disambiguator.resolve_interactively(
                    query,
                    keywords,
                    max_rounds=2
                )
            else:
                # Manual clarification without AI
                keywords = self._manual_clarification(keywords, issues, suggestions)
        else:
            print("   ✓ No ambiguities detected!")

        # Step 4: Generate SQL
        print("\n⚙️  Generating SQL query...")
        try:
            sql = self.processor.process(keywords)
            explanation = self.processor.explain_query(keywords, sql)

            print("\n" + "=" * 70)
            print("✅ RESULT:")
            print("=" * 70)
            print(f"\n📖 Explanation:")
            print(f"   {explanation}")
            print(f"\n💾 SQL Query:")
            print(f"   {sql}")
            print()

            # Show suggestions
            suggestions = self.processor.suggest_improvements(keywords)
            if suggestions:
                print("💡 Suggestions:")
                for suggestion in suggestions:
                    print(f"   {suggestion}")
                print()

            print("=" * 70)
            print()

            return sql

        except Exception as e:
            print(f"\n❌ Error generating SQL: {e}")
            return None

    def _manual_clarification(self, keywords: Dict, issues: List[str], suggestions: Dict) -> Dict:
        """Manual clarification without AI when API is not available"""
        print("\n🤔 Manual clarification needed:")

        if "missing_column" in issues or "ranking_without_column" in issues:
            cols = suggestions.get('numeric_columns', [])
            if cols:
                print(f"\n   Which column should I use?")
                for i, col in enumerate(cols, 1):
                    print(f"   {i}. {col}")

                choice = input("\n   Enter number or column name: ").strip()

                # Parse choice
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(cols):
                        keywords['primary_column'] = cols[choice_idx]
                        keywords['column_confidence'] = 100.0
                except ValueError:
                    # User entered column name
                    if choice.lower() in cols:
                        keywords['primary_column'] = choice.lower()
                        keywords['column_confidence'] = 100.0

        return keywords

    def run(self):
        """Main application loop"""
        self.print_banner()

        # Check if we should show help on first run
        first_run = True

        while True:
            try:
                # Get user input
                if first_run:
                    print("Type a query or 'help' for examples:")
                    first_run = False

                query = input("\n🔵 Query: ").strip()

                if not query:
                    continue

                # Handle commands
                if query.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break

                elif query.lower() == 'help':
                    self.print_help()
                    continue

                elif query.lower() in ['tables', 'schema']:
                    self.print_tables()
                    continue

                # Process the query
                sql = self.process_query(query)

                # Optional: Ask if user wants to see another query
                # (Removed to allow continuous querying)

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!\n")
                break

            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Please try again or type 'exit' to quit.\n")


def main():
    """Entry point"""
    app = InteractiveNLPApp()
    app.run()


if __name__ == "__main__":
    main()
