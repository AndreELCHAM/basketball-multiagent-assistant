import os
import sys
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.supervisor import supervisor_llm_route
from src.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DATA_DIR

load_dotenv()


ROUTING_TEST_CASES = [
    {
        "query": "What is the penalty for a clear path foul in the NBA?",
        "description": "RAG Single League (NBA specified)",
        "expected_agents": ["rag_agent"],
        "expected_needs_league": False,
    },
    {
        "query": "How do the traveling rules differ between FIBA and the NBA?",
        "description": "RAG Multi-League Comparison",
        "expected_agents": ["rag_agent"],
        "expected_needs_league": False,
    },
    {
        "query": "What is the definition of an unsportsmanlike foul?",
        "description": "RAG Missing League — should trigger league prompt",
        "expected_agents": ["rag_agent"],
        "expected_needs_league": True,
    },
    {
        "query": "Who is currently leading the NBA in scoring this season?",
        "description": "Pure Web Search — live stats",
        "expected_agents": ["web_agent"],
        "expected_needs_league": False,
    },
    {
        "query": "How many points did LeBron score yesterday?",
        "description": "Web Search — recent game stats",
        "expected_agents": ["web_agent"],
        "expected_needs_league": False,
    },
    {
        "query": "Luka Doncic picked up his 14th technical foul last night. Is he in danger of getting suspended in the NBA?",
        "description": "Web + Suspension MCP",
        "expected_agents": ["web_agent", "mcp_suspension"],
        "expected_needs_league": False,
    },
    {
        "query": "What would be Nikola Jokic's performance score for his game against the Lakers last night?",
        "description": "Web + Performance MCP",
        "expected_agents": ["web_agent", "mcp_performance"],
        "expected_needs_league": False,
    },
    {
        "query": "Grade the performance of LeBron James in his most recent game",
        "description": "Web + Performance MCP (implicit stats needed)",
        "expected_agents": ["web_agent", "mcp_performance"],
        "expected_needs_league": False,
    },
]


def evaluate_routing():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_key_here":
        print(" Error: Valid OPENROUTER_API_KEY not found in .env")
        return

    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key
    )

    print("=" * 70)
    print("AGENT ROUTING EVALUATION")
    print("=" * 70)

    correct_agents = 0
    correct_league = 0
    total = len(ROUTING_TEST_CASES)
    results = []

    for i, test in enumerate(ROUTING_TEST_CASES, 1):
        query = test["query"]
        print(f"\n[Test {i}/{total}] {test['description']}")
        print(f"  Query: {query}")

        try:
            plan = supervisor_llm_route(client, query)

            # Extract actual agents from the plan list
            actual_agents = plan.get("plan", [])

            actual_needs_league = plan.get("league") == "ASK_USER"

            # Evaluate agent selection
            expected_set = set(test["expected_agents"])
            actual_set = set(actual_agents)
            agents_correct = expected_set == actual_set

            # Evaluate league prompt
            league_correct = actual_needs_league == test["expected_needs_league"]

            if agents_correct:
                correct_agents += 1
            if league_correct:
                correct_league += 1

            status = "✅" if agents_correct else "❌"
            league_status = "✅" if league_correct else "❌"

            print(f"  Expected agents: {sorted(test['expected_agents'])}")
            print(f"  Actual agents:   {sorted(actual_agents)} {status}")
            print(f"  League prompt:   expected={test['expected_needs_league']}, actual={actual_needs_league} {league_status}")

            results.append({
                "query": query,
                "description": test["description"],
                "expected_agents": sorted(test["expected_agents"]),
                "actual_agents": sorted(actual_agents),
                "agents_correct": agents_correct,
                "expected_needs_league": test["expected_needs_league"],
                "actual_needs_league": actual_needs_league,
                "league_correct": league_correct,
                "full_plan": plan,
            })

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "query": query,
                "description": test["description"],
                "expected_agents": sorted(test["expected_agents"]),
                "actual_agents": [],
                "agents_correct": False,
                "expected_needs_league": test["expected_needs_league"],
                "actual_needs_league": None,
                "league_correct": False,
                "error": str(e),
            })

    # Summary
    agent_accuracy = correct_agents / total * 100
    league_accuracy = correct_league / total * 100

    print("\n" + "=" * 70)
    print("ROUTING EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Agent Selection Accuracy: {correct_agents}/{total} ({agent_accuracy:.1f}%)")
    print(f"League Prompt Accuracy:   {correct_league}/{total} ({league_accuracy:.1f}%)")
    print(f"Overall Accuracy:         {(correct_agents + correct_league)}/{total * 2} ({(agent_accuracy + league_accuracy) / 2:.1f}%)")
    print("=" * 70)

    # Save results
    results_path = DATA_DIR / "routing_evaluation_results.md"
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("# Agent Routing Evaluation Results\n\n")
        f.write(f"**Agent Selection Accuracy:** {correct_agents}/{total} ({agent_accuracy:.1f}%)\n\n")
        f.write(f"**League Prompt Accuracy:** {correct_league}/{total} ({league_accuracy:.1f}%)\n\n")
        f.write(f"**Overall Accuracy:** {(correct_agents + correct_league)}/{total * 2} ({(agent_accuracy + league_accuracy) / 2:.1f}%)\n\n")

        f.write("## Detailed Results\n\n")
        from tabulate import tabulate
        table = [
            {
                "Test": r["description"],
                "Agents": "✅" if r["agents_correct"] else f"❌ got {r['actual_agents']}",
                "League": "✅" if r["league_correct"] else f"❌ got {r['actual_needs_league']}",
            }
            for r in results
        ]
        f.write(tabulate(table, headers="keys", tablefmt="github"))
        f.write("\n\n")

        f.write("## Full Routing Plans\n\n")
        for r in results:
            f.write(f"### {r['description']}\n")
            f.write(f"**Query:** {r['query']}\n\n")
            if "full_plan" in r:
                f.write(f"```json\n{json.dumps(r['full_plan'], indent=2)}\n```\n\n")
            if "error" in r:
                f.write(f"**Error:** {r['error']}\n\n")

    print(f"\nResults saved to {results_path}")

    # Save raw JSON
    json_path = DATA_DIR / "routing_evaluation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)


if __name__ == "__main__":
    evaluate_routing()
