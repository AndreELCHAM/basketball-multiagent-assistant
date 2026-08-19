"""
Supervisor / Routing node for System A.
- Detects user language
- Translates to English if needed
- Extracts league context
- Routes to the appropriate agent (or directly to RAG in rag_only mode)
"""

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
    """Create OpenRouter client."""
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def detect_language(text: str) -> str:
    """Detect the language of input text. Returns ISO 639-1 code."""
    try:
        lang = detect(text)
        # Normalize common codes
        lang_map = {"en": "en", "fr": "fr", "es": "es", "ar": "ar"}
        return lang_map.get(lang, lang)
    except LangDetectException:
        return "en"


def extract_league_regex(text: str) -> Optional[str]:
    """Extract league from query using pattern matching."""
    text_lower = text.lower()

    patterns = {
        "FIBA_3x3": [r"\b3[x×]3\b", r"\bfiba\s*3[x×]3\b", r"\b3\s*on\s*3\b"],
        "NBA": [r"\bnba\b"],
        "NCAA": [r"\bncaa\b", r"\bcollege\b"],
        "FIBA": [r"\bfiba\b"],
    }

    # Check 3x3 first (more specific than FIBA)
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
    """Translate text to English via LLM."""
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
def supervisor_llm_route(client: OpenAI, english_query: str) -> dict:
    """
    Full supervisor mode: LLM reasons about the query and decides routing.
    Returns {"next_agent": str, "league_filter": str|None, "rewritten_query": str}
    """
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a routing supervisor for a basketball rules assistant. "
                    "Given a user query about basketball rules, you must decide:\n"
                    "1. Which agent to route to:\n"
                    "   - 'rag_agent': For questions about official basketball rules, regulations, "
                    "court dimensions, procedures, signals, etc.\n"
                    "   - 'web_agent': For live game stats, recent news, current rosters.\n"
                    "   - 'mcp_tools': For deterministic calculations (foul accumulation, tiebreakers).\n"
                    "2. Which league the question is about: 'FIBA', 'NBA', 'NCAA', 'FIBA_3x3', or null.\n"
                    "3. Rewrite the query in a clear, precise form suitable for retrieval.\n\n"
                    "Respond in EXACTLY this format (no extra text):\n"
                    "AGENT: <agent_name>\n"
                    "LEAGUE: <league_or_null>\n"
                    "QUERY: <rewritten_query>"
                ),
            },
            {"role": "user", "content": english_query},
        ],
        max_tokens=256,
        temperature=0.0,
    )

    text = response.choices[0].message.content.strip()
    result = {"next_agent": "rag_agent", "league_filter": None, "rewritten_query": english_query}

    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("AGENT:"):
            agent = line.split(":", 1)[1].strip().lower()
            if agent in ("rag_agent", "web_agent", "mcp_tools"):
                result["next_agent"] = agent
        elif line.startswith("LEAGUE:"):
            league = line.split(":", 1)[1].strip()
            if league.upper() in ("FIBA", "NBA", "NCAA", "FIBA_3X3"):
                result["league_filter"] = league.upper()
            elif league.lower() != "null" and league.lower() != "none":
                result["league_filter"] = league.upper()
        elif line.startswith("QUERY:"):
            result["rewritten_query"] = line.split(":", 1)[1].strip()

    return result


def supervisor_node(state: AgentState) -> dict:
    """
    Supervisor node for the LangGraph workflow.

    In rag_only mode: detects language, translates, extracts league via regex,
    routes straight to rag_agent (no LLM routing call).

    In full mode: additionally calls LLM for intelligent routing and query rewriting.
    """
    user_query = state["user_query"]
    iteration = state.get("iteration_count", 0)

    logger.info(f"Supervisor (iteration {iteration}): processing query")

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
        # Lightweight: regex league extraction, direct to RAG
        league = extract_league_regex(english_query)
        logger.info(f"  [rag_only mode] League={league}, routing to rag_agent")
        return {
            "user_language": user_language,
            "english_query": english_query,
            "league_filter": league,
            "next_agent": "rag_agent",
            "iteration_count": iteration + 1,
        }
    else:
        # Full mode: LLM-based routing
        client = _get_llm_client()
        route_result = supervisor_llm_route(client, english_query)
        logger.info(
            f"  [full mode] Agent={route_result['next_agent']}, "
            f"League={route_result['league_filter']}"
        )
        return {
            "user_language": user_language,
            "english_query": route_result["rewritten_query"],
            "league_filter": route_result["league_filter"],
            "next_agent": route_result["next_agent"],
            "iteration_count": iteration + 1,
        }
