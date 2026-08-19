"""
System A entry point.
Run the LangGraph RAG workflow via CLI single-query or interactive REPL mode.
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.graph import run_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def print_result(state: dict):
    """Pretty-print the query result."""
    print("\n" + "=" * 60)
    print("SYSTEM A RESPONSE")
    print("=" * 60)

    lang = state.get("user_language", "en")
    eq = state.get("english_query", "")
    answer = state.get("final_answer", "No answer generated.")
    chunks = state.get("retrieved_chunks", [])
    images = state.get("image_paths", [])
    league = state.get("league_filter", "None")

    print(f"\n📌 Detected Language: {lang}")
    print(f"📌 League Filter: {league}")
    if eq and eq != state.get("user_query", ""):
        print(f"📌 English Query: {eq}")

    print(f"\n📚 Retrieved {len(chunks)} chunks")
    if chunks:
        for i, chunk in enumerate(chunks[:3], 1):
            meta = chunk.get("metadata", {})
            section = meta.get("article_or_section", "?")
            score = chunk.get("score", 0)
            print(f"   [{i}] {meta.get('league', '?')} — {section} (score: {score:.3f})")

    if images:
        print(f"\n🖼️  Referenced Diagrams:")
        for img in images:
            print(f"   → {img}")

    print(f"\n💬 Answer:\n")
    print(answer)
    print("\n" + "=" * 60)


def run_interactive():
    """Interactive REPL mode."""
    print("\n" + "=" * 60)
    print("Basketball Rules Assistant — System A (Interactive)")
    print("=" * 60)
    print("Type your question about basketball rules.")
    print("Prefix with [FIBA], [NBA], [NCAA], or [3x3] for league-specific queries.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            query = input("🏀 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query or query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        # Check for league prefix override
        league = None
        for prefix, league_val in [("[fiba]", "FIBA"), ("[nba]", "NBA"),
                                    ("[ncaa]", "NCAA"), ("[3x3]", "FIBA_3x3")]:
            if query.lower().startswith(prefix):
                league = league_val
                query = query[len(prefix):].strip()
                break

        try:
            state = run_query(query, league=league)
            print_result(state)
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            print(f"\n❌ Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="System A — Basketball Rules RAG")
    parser.add_argument("--query", "-q", type=str, help="Single query to process")
    parser.add_argument("--league", "-l", type=str, default=None,
                        choices=["FIBA", "NBA", "NCAA", "FIBA_3x3"],
                        help="League filter")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Run in interactive REPL mode")
    args = parser.parse_args()

    if args.interactive:
        run_interactive()
    elif args.query:
        state = run_query(args.query, league=args.league)
        print_result(state)
    else:
        # Default to interactive
        run_interactive()


if __name__ == "__main__":
    main()
