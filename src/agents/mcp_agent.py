
import logging

import httpx
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    MCP_SUSPENSION_URL,
    MCP_PERFORMANCE_URL,
)
from src.agents.state import AgentState

logger = logging.getLogger(__name__)


def _get_llm_client() -> OpenAI:

    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
)
def _call_suspension_calculator(params: dict) -> dict:
    url = f"{MCP_SUSPENSION_URL}/calculate-suspension"
    logger.info(f"  Calling suspension calculator at {url}")
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=params)
        response.raise_for_status()
        return response.json()


def mcp_suspension_node(state: AgentState) -> dict:

    tool_input = state.get("tool_input", {})
    web_results = state.get("web_search_results", {})
    user_language = state.get("user_language", "en")
    english_query = state.get("english_query", "")

    logger.info(f"MCP Suspension Node: input={tool_input}")

    if web_results and web_results.get("player_stats"):
        stats = web_results["player_stats"]
        for key in ["fouls_committed", "games_played", "total_season_games", "league"]:
            if key not in tool_input or tool_input.get(key) is None:
                if key in stats:
                    tool_input[key] = stats[key]

    league = tool_input.get("league", state.get("league_filter", "NBA"))
    params = {
        "fouls_committed": tool_input.get("fouls_committed", 0),
        "games_played": tool_input.get("games_played", 0),
        "total_season_games": tool_input.get("total_season_games", 82),
        "foul_threshold": tool_input.get("foul_threshold", 16),
        "league": league,
    }

    try:
        mcp_result = _call_suspension_calculator(params)
        logger.info(f"  Suspension result: {mcp_result}")
    except Exception as e:
        logger.error(f"  Suspension calculator failed: {e}")
        mcp_result = {"error": str(e)}

    answer = _synthesize_mcp_answer(
        english_query, "suspension_probability", mcp_result, params, user_language
    )

    return {
        "mcp_results": mcp_result,
        "final_answer": answer,
        "next_agent": "__end__",
        "response_type": "answer",
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
)
def _call_performance_calculator(params: dict) -> dict:
    url = f"{MCP_PERFORMANCE_URL}/calculate-performance"
    logger.info(f"  Calling performance calculator at {url}")
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=params)
        response.raise_for_status()
        return response.json()


def mcp_performance_node(state: AgentState) -> dict:
    tool_input = state.get("tool_input", {})
    web_results = state.get("web_search_results", {})
    user_language = state.get("user_language", "en")
    english_query = state.get("english_query", "")

    logger.info(f"MCP Performance Node: input={tool_input}")

    if web_results and web_results.get("player_stats"):
        stats = web_results["player_stats"]
        stat_fields = [
            "points", "rebounds", "assists", "steals", "blocks",
            "turnovers", "fg_made", "fg_attempted", "ft_made",
            "ft_attempted", "minutes", "personal_fouls",
            "offensive_rebounds", "defensive_rebounds",
        ]
        for key in stat_fields:
            if key not in tool_input or tool_input.get(key) is None:
                if key in stats:
                    tool_input[key] = stats[key]

    params = {
        "points": tool_input.get("points", 0),
        "rebounds": tool_input.get("rebounds", 0),
        "assists": tool_input.get("assists", 0),
        "steals": tool_input.get("steals", 0),
        "blocks": tool_input.get("blocks", 0),
        "turnovers": tool_input.get("turnovers", 0),
        "fg_made": tool_input.get("fg_made", 0),
        "fg_attempted": tool_input.get("fg_attempted", 0),
        "ft_made": tool_input.get("ft_made", 0),
        "ft_attempted": tool_input.get("ft_attempted", 0),
        "minutes": tool_input.get("minutes", 0),
        "personal_fouls": tool_input.get("personal_fouls", 0),
        "offensive_rebounds": tool_input.get("offensive_rebounds", 0),
        "defensive_rebounds": tool_input.get("defensive_rebounds", 0),
    }

    try:
        mcp_result = _call_performance_calculator(params)
        logger.info(f"  Performance result: {mcp_result}")
    except Exception as e:
        logger.error(f"  Performance calculator failed: {e}")
        mcp_result = {"error": str(e)}

    answer = _synthesize_mcp_answer(
        english_query, "player_performance", mcp_result, params, user_language
    )

    return {
        "mcp_results": mcp_result,
        "final_answer": answer,
        "next_agent": "__end__",
        "response_type": "answer",
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
)
def _synthesize_mcp_answer(
    query: str,
    tool_type: str,
    result: dict,
    params: dict,
    user_language: str,
) -> str:
    client = _get_llm_client()

    language_instruction = ""
    if user_language != "en":
        lang_names = {"fr": "French", "es": "Spanish", "ar": "Arabic"}
        lang_name = lang_names.get(user_language, user_language)
        language_instruction = (
            f"\n\nIMPORTANT: The user's language is {lang_name}. "
            f"You MUST write your final answer in {lang_name}."
        )

    if tool_type == "suspension_probability":
        system_prompt = (
            "You are a basketball analytics expert. The user asked about suspension risk. "
            "You have the results from a deterministic suspension probability calculator. "
            "Present the findings clearly with the key numbers, risk level, and a brief "
            "explanation of what this means for the player's season. "
            "Be precise and reference the specific numbers."
            f"{language_instruction}"
        )
    else:
        system_prompt = (
            "You are a basketball analytics expert. The user asked about player performance. "
            "You have the results from a performance scoring calculator. "
            "Present the game score, efficiency rating, grade, and analysis in a clear, "
            "engaging format. Compare to typical NBA/league benchmarks when relevant."
            f"{language_instruction}"
        )

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"User question: {query}\n\n"
                    f"Calculator input: {params}\n\n"
                    f"Calculator result: {result}"
                ),
            },
        ],
        max_tokens=1024,
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()
