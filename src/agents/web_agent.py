
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import SYSTEM_B_URL
from src.agents.state import AgentState

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
)
def _call_system_b(query: str, league: str = None) -> dict:
    url = f"{SYSTEM_B_URL}/search"
    payload = {"query": query}
    if league:
        payload["league"] = league

    logger.info(f"  Calling System B at {url}")
    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def web_agent_node(state: AgentState) -> dict:

    english_query = state.get("english_query", "")
    rewritten_queries = state.get("rewritten_queries", {})
    web_query = rewritten_queries.get("web_agent", english_query)
    league_filter = state.get("league_filter")

    logger.info(f"Web Agent: query='{web_query[:80]}...', league={league_filter}")

    try:
        web_results = _call_system_b(web_query, league_filter)
        logger.info(f"  System B returned: {list(web_results.keys())}")
    except Exception as e:
        logger.error(f"  System B call failed: {e}")
        web_results = {
            "status": "error",
            "error": str(e),
            "results": [],
        }

    route_plan = state.get("route_plan", [])

    if route_plan:
        # More steps ahead return to supervisor for re-routing
        logger.info(f"  Web data collected, re-routing (plan: {route_plan})")
        return {
            "web_search_results": web_results,
            "next_agent": "supervisor",
        }
    else:
        # No more steps format web results as the final answer
        logger.info("  Web data is the final output, formatting answer")
        answer = _format_web_answer(web_results, state.get("user_language", "en"))
        return {
            "web_search_results": web_results,
            "final_answer": answer,
            "next_agent": "__end__",
            "response_type": "answer",
        }


def _format_web_answer(web_results: dict, user_language: str) -> str:
    if web_results.get("status") == "error":
        return f"I was unable to fetch live data: {web_results.get('error', 'Unknown error')}"

    answer = web_results.get("answer", "")
    if answer:
        if user_language != "en":
            from src.agents.supervisor import translate_to_language, _get_llm_client
            client = _get_llm_client()
            answer = translate_to_language(client, answer, user_language)
        return answer

    results = web_results.get("results", [])
    if not results:
        return "I couldn't find relevant live data for your question."

    parts = ["Here's what I found:\n"]
    for i, r in enumerate(results[:5], 1):
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        parts.append(f"{i}. **{title}**\n   {snippet}")

    return "\n\n".join(parts)
