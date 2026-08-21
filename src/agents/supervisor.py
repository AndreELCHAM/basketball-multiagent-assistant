
import json
import logging
import re
from typing import Optional

from langdetect import detect, LangDetectException
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    ROUTE_MODE,
)
from src.agents.state import AgentState

logger = logging.getLogger(__name__)


def _get_llm_client() -> OpenAI:
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        # Normalize common codes
        lang_map = {"en": "en", "fr": "fr", "es": "es", "ar": "ar"}
        return lang_map.get(lang, lang)
    except LangDetectException:
        return "en"


def extract_league_regex(text: str) -> Optional[str]:
    text_lower = text.lower()

    patterns = {
        "FIBA_3x3": [r"\b3[x×]3\b", r"\bfiba\s*3[x×]3\b", r"\b3\s*on\s*3\b"],
        "NBA": [r"\bnba\b"],
        "NCAA": [r"\bncaa\b", r"\bcollege\b"],
        "FIBA": [r"\bfiba\b"],
    }

    for league, league_patterns in patterns.items():
        for pattern in league_patterns:
            if re.search(pattern, text_lower):
                return league

    return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
)
def translate_to_english(client: OpenAI, text: str, source_lang: str) -> str:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise translator. Translate the following text to English. "
                    "Preserve all technical basketball terminology. Output ONLY the translation, "
                    "nothing else."
                ),
            },
            {"role": "user", "content": text},
        ],
        max_tokens=512,
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
)
def translate_to_language(client: OpenAI, text: str, target_lang: str) -> str:
    lang_names = {"fr": "French", "es": "Spanish", "ar": "Arabic"}
    lang_name = lang_names.get(target_lang, target_lang)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a precise translator. Translate the following text to {lang_name}. "
                    "Preserve all technical basketball terminology. Output ONLY the translation, "
                    "nothing else."
                ),
            },
            {"role": "user", "content": text},
        ],
        max_tokens=512,
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()


ROUTING_SYSTEM_PROMPT = """You are a routing supervisor for a multi-agent basketball rules and analytics assistant.

You have access to these agents:
1. **rag_agent**: For questions about official basketball rules, regulations, court dimensions, procedures, referee signals, etc. Uses vector search over FIBA, NBA, NCAA, and FIBA 3x3 rulebooks.
2. **web_agent**: For live/current information — recent game stats, current season data, player performance this season, recent news, trade rumors, injury updates. Anything that requires up-to-date internet data.
3. **mcp_suspension**: Deterministic calculator for suspension probability. Use when the query involves predicting whether a player will be suspended based on their foul/technical accumulation. Requires: fouls_committed, games_played, total_season_games, foul_threshold, league.
4. **mcp_performance**: Deterministic calculator for rating a player's game performance. Use when asked to score/rate/evaluate a player's statistical performance. Requires game stats like points, rebounds, assists, etc.

ROUTING RULES:
- If the query asks about rules/regulations → rag_agent
- If the query needs live stats, current rosters, recent games → web_agent
- If the query asks about suspension risk/probability → may need web_agent FIRST (to get stats), THEN mcp_suspension
- If the query asks to rate/score a player's performance → may need web_agent FIRST (to get stats), THEN mcp_performance
- If the query compares rules across leagues → rag_agent (with split queries noted)
- If the query combines rule knowledge AND live data → plan multiple steps

For LEAGUE detection:
- Extract the league if mentioned: "NBA", "FIBA", "NCAA", "FIBA_3x3"
- If NO league is detectable AND the query needs rag_agent → set league to "ASK_USER"
- If the query goes to web_agent first → set league to "DETECT_FROM_WEB" (the web results will reveal the league)

Respond in EXACTLY this JSON format (no markdown, no extra text):
{
  "plan": ["agent1", "agent2"],
  "league": "NBA|FIBA|NCAA|FIBA_3x3|ASK_USER|DETECT_FROM_WEB|null",
  "queries": {
    "agent1": "rewritten query for agent1",
    "agent2": "rewritten query or structured params for agent2"
  },
  "tool_input": {
    "param1": "value1"
  },
  "reasoning": "Brief explanation of routing decision"
}

For mcp_suspension tool_input, extract these fields when available:
- fouls_committed (int), games_played (int), total_season_games (int), foul_threshold (int), league (str)

For mcp_performance tool_input, extract these fields when available:
- points, rebounds, assists, steals, blocks, turnovers, fg_made, fg_attempted, ft_made, ft_attempted, minutes, personal_fouls, offensive_rebounds, defensive_rebounds (all int/float)

CRITICAL RULE FOR MCP ROUTING:
If the user's query asks for an MCP tool calculation but is MISSING required variables (like games played, current season stats, minutes played), you MUST route to `web_agent` first to fetch them. 
- The plan MUST be `["web_agent", "mcp_suspension"]` or `["web_agent", "mcp_performance"]`.
- Put the web search query in `queries.web_agent`.
- Only route directly to an MCP tool (`["mcp_suspension"]`) if EVERY required input variable is explicitly provided in the user's query.
- DO NOT output `null` values in `tool_input`. Only include keys that you have explicitly extracted from the user's text.
- DO NOT hallucinate fake values (like `games_played: 1`) just to fill out the parameters. If a number is not stated in the prompt, you do not have it.

Example of MISSING inputs handling:
User: "Draymond Green has 15 technical fouls. Will he be suspended?"
Output:
{
  "plan": ["web_agent", "mcp_suspension"],
  "league": "NBA",
  "queries": {
    "web_agent": "Draymond Green games played and stats current season"
  },
  "tool_input": {
    "fouls_committed": 15
  },
  "reasoning": "Missing games played. Routing to web_agent to fetch stats first."
}

For cross-league comparisons (e.g., "Compare NBA vs FIBA traveling rules"), use:
{
  "plan": ["rag_agent"],
  "league": "MULTI",
  "queries": {
    "rag_agent_NBA": "traveling violation rules and definition",
    "rag_agent_FIBA": "traveling violation rules and definition"
  }
}"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
)
def supervisor_llm_route(client: OpenAI, english_query: str, conversation_context: str = "") -> dict:

    try:
        from datetime import datetime
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        messages = [
            {"role": "system", "content": ROUTING_SYSTEM_PROMPT + f"\n\nIMPORTANT: Today's date is {current_date}. Keep this in mind when rewriting queries with relative time (like 'today' or 'yesterday')."},
        ]

        if conversation_context:
            messages.append({
                "role": "system",
                "content": f"Recent conversation context:\n{conversation_context}",
            })

        messages.append({"role": "user", "content": english_query})

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.0,
        )

        if not response.choices:
            logger.warning(f"OpenRouter returned empty choices. Falling back. Response: {response}")
            text = ""
        else:
            content = response.choices[0].message.content
            text = content.strip() if content else ""

        try:
            if not text:
                raise ValueError("Empty LLM response")
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            result = json.loads(text)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse supervisor JSON response: {e}")
            result = _fallback_parse(text, english_query)

        valid_agents = {"rag_agent", "web_agent", "mcp_suspension", "mcp_performance"}
        plan = result.get("plan", ["rag_agent"])
        plan = [a for a in plan if a in valid_agents] or ["rag_agent"]

        valid_leagues = {"NBA", "FIBA", "NCAA", "FIBA_3X3", "FIBA_3x3", "ASK_USER", "DETECT_FROM_WEB", "MULTI"}
        league = result.get("league")
        if league and league.upper() not in valid_leagues and league not in valid_leagues:
            league = None
        elif league:
            league = league.upper()
            if league == "FIBA_3X3":
                league = "FIBA_3x3" 

        return {
            "plan": plan,
            "league": league,
            "queries": result.get("queries", {}),
            "tool_input": result.get("tool_input", {}),
            "reasoning": result.get("reasoning", ""),
        }
    except Exception as e:
        import traceback
        logger.error(f"Error inside supervisor_llm_route: {traceback.format_exc()}")
        raise


def _fallback_parse(text: str, english_query: str) -> dict:
    result = {
        "plan": ["rag_agent"],
        "league": None,
        "queries": {"rag_agent": english_query},
        "tool_input": {},
        "reasoning": "Fallback parse — routing to RAG by default",
    }
    for agent in ["web_agent", "mcp_suspension", "mcp_performance", "rag_agent"]:
        if agent in text.lower():
            result["plan"] = [agent]
            break

    for league in ["NBA", "FIBA", "NCAA", "FIBA_3X3"]:
        if league.lower() in text.lower():
            result["league"] = league
            break

    return result


def _build_conversation_context(conversation_history: list[dict], max_messages: int = 6) -> str:
    if not conversation_history:
        return ""
    recent = conversation_history[-max_messages:]
    parts = []
    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


def supervisor_node(state: AgentState) -> dict:

    user_query = state["user_query"]
    iteration = state.get("iteration_count", 0)

    logger.info(f"Supervisor (iteration {iteration}): processing query")


    if state.get("web_search_results") and state.get("route_plan"):
        return _handle_reentry(state)

    # Step 1: Detect language
    user_language = detect_language(user_query)
    logger.info(f"  Detected language: {user_language}")

    # Step 2: Translate to English if needed
    if user_language != "en":
        client = _get_llm_client()
        english_query = translate_to_english(client, user_query, user_language)
        logger.info(f"  Translated to English: {english_query[:100]}...")
    else:
        english_query = user_query

    # Step 3: Route
    if ROUTE_MODE == "rag_only":
        league = extract_league_regex(english_query)
        logger.info(f"  [rag_only mode] League={league}, routing to rag_agent")
        return {
            "user_language": user_language,
            "english_query": english_query,
            "league_filter": league,
            "next_agent": "rag_agent",
            "route_plan": [],
            "rewritten_queries": {"rag_agent": english_query},
            "tool_input": {},
            "iteration_count": iteration + 1,
            "response_type": "answer",
        }
    else:
        provided_league = state.get("league_filter")
        
        client = _get_llm_client()
        conversation_context = _build_conversation_context(
            state.get("conversation_history", [])
        )
        route_result = supervisor_llm_route(client, english_query, conversation_context)

        logger.info(
            f"  [full mode] Plan={route_result['plan']}, "
            f"League={route_result['league']}, "
            f"Reasoning={route_result['reasoning']}"
        )

        plan = route_result["plan"]
        league = route_result["league"]
        
        # Override the LLM's league decision if a league was explicitly provided (e.g., recovered from human input)
        if provided_league and provided_league not in ("ASK_USER", "DETECT_FROM_WEB", "MULTI", None):
            logger.info(f"  Overriding LLM league decision '{league}' with provided league '{provided_league}'")
            league = provided_league

        queries = route_result["queries"]
        tool_input = route_result["tool_input"]

        # Handle league detection
        if league == "ASK_USER":
            logger.info("  League unknown — requesting human input")


            prompt_msg = "Which league is your question about?"
            if user_language != "en":
                prompt_msg = translate_to_language(client, prompt_msg, user_language)

            return {
                "user_language": user_language,
                "english_query": english_query,
                "league_filter": None,
                "next_agent": "human_input",
                "route_plan": plan,
                "rewritten_queries": queries,
                "tool_input": tool_input,
                "pending_human_input": "league_selection",
                "human_input_options": ["NBA", "FIBA", "NCAA", "FIBA_3x3"],
                "human_input_message": prompt_msg,
                "iteration_count": iteration + 1,
                "response_type": "league_prompt",
            }

        # Handle multi-league comparison
        if league == "MULTI":
            logger.info("  Multi-league comparison detected")
            return {
                "user_language": user_language,
                "english_query": english_query,
                "league_filter": "MULTI",
                "next_agent": "rag_agent",
                "route_plan": [],
                "rewritten_queries": queries,
                "tool_input": {},
                "iteration_count": iteration + 1,
                "response_type": "answer",
            }


        first_agent = plan[0]
        remaining_plan = plan[1:] if len(plan) > 1 else []


        resolved_league = None
        if league and league not in ("DETECT_FROM_WEB", "MULTI"):
            resolved_league = league

        return {
            "user_language": user_language,
            "english_query": english_query,
            "league_filter": resolved_league,
            "next_agent": first_agent,
            "route_plan": remaining_plan,
            "rewritten_queries": queries,
            "tool_input": tool_input,
            "iteration_count": iteration + 1,
            "response_type": "answer",
        }


def _handle_reentry(state: AgentState) -> dict:

    iteration = state.get("iteration_count", 0)
    route_plan = state.get("route_plan", [])
    web_results = state.get("web_search_results", {})
    tool_input = state.get("tool_input", {})

    logger.info(f"  Supervisor re-entry: remaining plan={route_plan}")

    # Try to extract league from web results if not already set
    league_filter = state.get("league_filter")
    if not league_filter and web_results:
        detected_league = web_results.get("league")
        if detected_league:
            league_filter = detected_league
            logger.info(f"  League detected from web results: {league_filter}")

    # Enrich tool_input with web data for MCP tools
    web_stats = web_results.get("player_stats", {})
    if web_stats:
        for key, value in web_stats.items():
            if key not in tool_input or tool_input[key] is None:
                tool_input[key] = value

    if route_plan:
        next_agent = route_plan[0]
        remaining = route_plan[1:]
        logger.info(f"  Re-routing to: {next_agent}")
        return {
            "next_agent": next_agent,
            "route_plan": remaining,
            "tool_input": tool_input,
            "league_filter": league_filter,
            "iteration_count": iteration + 1,
        }
    else:
        logger.info("  No more steps in plan, ending")
        return {
            "next_agent": "__end__",
            "route_plan": [],
            "tool_input": tool_input,
            "league_filter": league_filter,
            "iteration_count": iteration + 1,
        }
