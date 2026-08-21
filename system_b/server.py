
import logging
import os
import re
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

app = FastAPI(
    title="System B — Live Web Search Agent (Google ADK)",
    description="Google ADK-based agent for live basketball data retrieval",
    version="2.0.0",
)



class SearchRequest(BaseModel):
    query: str
    league: Optional[str] = None


class PlayerStatsRequest(BaseModel):
    player: Optional[str] = None
    team: Optional[str] = None
    league: Optional[str] = None
    stat_type: Optional[str] = "season"  # "season", "game", "career"



def _create_adk_client() -> genai.Client:

    return genai.Client(api_key=GOOGLE_API_KEY)


def _run_adk_search(query: str, extract_stats: bool = False) -> dict:

    client = _create_adk_client()

    from datetime import datetime
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    system_instruction = (
        "You are a basketball data research assistant. Your job is to find "
        "accurate, up-to-date basketball statistics and information.\n\n"
        f"IMPORTANT: Today's date is {current_date}. You MUST ensure that the data you retrieve is the most recent data available as of this date. If asked for 'last game', 'current season', or recent events, you MUST explicitly include the year {datetime.now().year} in your Google Search queries to avoid pulling outdated 2024/2025 data.\n\n"
        "When returning results:\n"
        "1. Always cite your sources\n"
        "2. Extract specific numbers and statistics when available\n"
        "3. Identify the league (NBA, FIBA, NCAA, etc.) from context\n"
        "4. If you find player stats, structure them clearly\n"
        "5. Be precise with dates and seasons\n\n"
    )

    if extract_stats:
        system_instruction += (
            "IMPORTANT: Extract numerical statistics in a structured format. "
            "For player stats, extract: points, rebounds, assists, steals, blocks, "
            "turnovers, field goals made/attempted, free throws made/attempted, "
            "games played, technical fouls, personal fouls, minutes per game.\n"
            "Format extracted stats as a clear list with labels."
        )

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1,
            ),
        )

        # Extract the text response
        answer_text = ""
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    answer_text += part.text

        # Extract grounding metadata (sources)
        sources = []
        grounding_metadata = getattr(response.candidates[0], 'grounding_metadata', None)
        if grounding_metadata:
            chunks = getattr(grounding_metadata, 'grounding_chunks', None)
            if chunks:
                for chunk in chunks:
                    web_chunk = getattr(chunk, 'web', None)
                    if web_chunk:
                        sources.append({
                            "title": getattr(web_chunk, 'title', ''),
                            "uri": getattr(web_chunk, 'uri', ''),
                        })

        # Try to detect league from the response
        detected_league = _detect_league_from_text(answer_text)

        # Try to extract structured stats from the response
        player_stats = {}
        if extract_stats and answer_text:
            # First try fast regex extraction
            player_stats = _extract_stats_from_text(answer_text)
            
            # If regex found too few stats, use LLM for reliable extraction
            if len(player_stats) < 3:
                logger.info(f"  Regex only found {len(player_stats)} stats, falling back to LLM extraction")
                llm_stats = _extract_stats_with_llm(client, answer_text)
                if llm_stats:
                    # Merge: LLM results fill in what regex missed
                    for key, value in llm_stats.items():
                        if key not in player_stats:
                            player_stats[key] = value
                    logger.info(f"  After LLM merge: {player_stats}")

        return {
            "status": "ok",
            "answer": answer_text,
            "results": sources,
            "league": detected_league,
            "player_stats": player_stats,
        }

    except Exception as e:
        logger.error(f"Google ADK search failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "answer": "",
            "results": [],
            "league": None,
            "player_stats": {},
        }


def _detect_league_from_text(text: str) -> Optional[str]:

    text_lower = text.lower()

    scores = {
        "NBA": len(re.findall(r'\bnba\b', text_lower)),
        "FIBA": len(re.findall(r'\bfiba\b', text_lower)),
        "NCAA": len(re.findall(r'\bncaa\b|\bcollege basketball\b', text_lower)),
        "FIBA_3x3": len(re.findall(r'\b3x3\b|\bfiba 3x3\b', text_lower)),
    }

    best_league = max(scores, key=scores.get)
    if scores[best_league] > 0:
        return best_league
    return None


def _extract_stats_with_llm(client, answer_text: str) -> dict:

    import json

    extraction_prompt = (
        "Extract the player's game statistics from the text below into a JSON object.\n"
        "Use ONLY these exact keys (omit any stat not found in the text):\n"
        "- points (int)\n"
        "- rebounds (int)\n"
        "- assists (int)\n"
        "- steals (int)\n"
        "- blocks (int)\n"
        "- turnovers (int)\n"
        "- fg_made (int) — field goals made\n"
        "- fg_attempted (int) — field goals attempted\n"
        "- ft_made (int) — free throws made\n"
        "- ft_attempted (int) — free throws attempted\n"
        "- minutes (float) — minutes played\n"
        "- personal_fouls (int)\n"
        "- offensive_rebounds (int)\n"
        "- defensive_rebounds (int)\n"
        "- games_played (int)\n"
        "- fouls_committed (int) — technical fouls\n\n"
        "RULES:\n"
        "- Output ONLY valid JSON, no markdown fences, no explanation.\n"
        "- Use integer or float values only, no strings.\n"
        "- If a stat is not mentioned in the text, do NOT include it.\n"
        "- If the text contains stats for multiple games, extract only the MOST RECENT single game.\n\n"
        f"Text:\n{answer_text}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=extraction_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
            ),
        )

        result_text = ""
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    result_text += part.text

        result_text = result_text.strip()
        # Strip markdown code fences if present
        if result_text.startswith("```"):
            result_text = re.sub(r"^```(?:json)?\s*", "", result_text)
            result_text = re.sub(r"\s*```$", "", result_text)

        stats = json.loads(result_text)

        # Validate: only keep known keys with numeric values
        valid_keys = {
            "points", "rebounds", "assists", "steals", "blocks",
            "turnovers", "fg_made", "fg_attempted", "ft_made",
            "ft_attempted", "minutes", "personal_fouls",
            "offensive_rebounds", "defensive_rebounds",
            "games_played", "fouls_committed",
        }
        cleaned = {}
        for key, value in stats.items():
            if key in valid_keys and isinstance(value, (int, float)):
                cleaned[key] = value

        logger.info(f"  LLM extracted stats: {cleaned}")
        return cleaned

    except Exception as e:
        logger.error(f"  LLM stat extraction failed: {e}")
        return {}


def _extract_stats_from_text(text: str) -> dict:

    stats = {}
    text_lower = text.lower()


    bi_patterns = {
        "points": [r'([\d.]+)[ \t]*(?:points|pts|ppg)', r'(?:points|pts|ppg)[ \t]*[:\-]?[ \t]*([\d.]+)'],
        "rebounds": [r'([\d.]+)[ \t]*(?:rebounds|reb|rpg)', r'(?:rebounds|reb|rpg)[ \t]*[:\-]?[ \t]*([\d.]+)'],
        "assists": [r'([\d.]+)[ \t]*(?:assists|ast|apg)', r'(?:assists|ast|apg)[ \t]*[:\-]?[ \t]*([\d.]+)'],
        "steals": [r'([\d.]+)[ \t]*(?:steals|stl|spg)', r'(?:steals|stl|spg)[ \t]*[:\-]?[ \t]*([\d.]+)'],
        "blocks": [r'([\d.]+)[ \t]*(?:blocks|blk|bpg)', r'(?:blocks|blk|bpg)[ \t]*[:\-]?[ \t]*([\d.]+)'],
        "turnovers": [r'([\d.]+)[ \t]*(?:turnovers|tov)', r'(?:turnovers|tov)[ \t]*[:\-]?[ \t]*([\d.]+)'],
        "minutes": [r'([\d.]+)[ \t]*(?:minutes|min|mpg)', r'(?:minutes[ \t]*(?:played)?|min|mpg)[ \t]*[:\-]?[ \t]*([\d.]+)'],
        "games_played": [r'([\d]+)[ \t]*(?:games?[ \t]*played|gp)', r'(?:games?[ \t]*played|gp)[ \t]*[:\-]?[ \t]*([\d]+)'],
        "personal_fouls": [r'([\d.]+)[ \t]*(?:personal fouls|pf)', r'(?:personal fouls|pf)[ \t]*[:\-]?[ \t]*([\d.]+)'],
        "fouls_committed": [r'([\d]+)[ \t]*(?:technical fouls?|technicals|techs)', r'(?:technical fouls?|technicals|techs)[ \t]*[:\-]?[ \t]*([\d]+)'],
    }

    for stat_name, patterns in bi_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                val = match.group(1)
                try:
                    stats[stat_name] = float(val) if '.' in val else int(val)
                except ValueError:
                    pass
                break  


    fg_match = re.search(r'(?:field goals?|fg)[ \t]*(?:made)?[/ \t]*(?:attempted)?[ \t]*[:\-]?[ \t]*(\d+)[ \t]*[/\-][ \t]*(\d+)', text_lower)
    if not fg_match:
        fg_match = re.search(r'(\d+)[ \t]*[/\-][ \t]*(\d+)[ \t]*(?:fg|field goals?|from the field)', text_lower)
    if fg_match:
        stats["fg_made"] = int(fg_match.group(1))
        stats["fg_attempted"] = int(fg_match.group(2))


    ft_match = re.search(r'(?:free throws?|ft)[ \t]*(?:made)?[/ \t]*(?:attempted)?[ \t]*[:\-]?[ \t]*(\d+)[ \t]*[/\-][ \t]*(\d+)', text_lower)
    if not ft_match:
        ft_match = re.search(r'(\d+)[ \t]*[/\-][ \t]*(\d+)[ \t]*(?:ft|free throws?|from the line)', text_lower)
    if ft_match:
        stats["ft_made"] = int(ft_match.group(1))
        stats["ft_attempted"] = int(ft_match.group(2))


    fg_pct_match = re.search(r'([\d.]+)%?\s*(?:fg%|field goal percentage|shooting percentage)', text_lower)
    if fg_pct_match:
        stats["fg_pct"] = float(fg_pct_match.group(1))

    logger.info(f"  Extracted stats from text: {stats}")
    return stats




@app.get("/health")
def health_check():
    """Health check endpoint for Docker orchestration."""
    return {
        "status": "ok",
        "system": "B",
        "framework": "Google ADK (Gemini + Google Search)",
        "has_api_key": bool(GOOGLE_API_KEY),
    }


@app.post("/search")
def search(request: SearchRequest):

    query = request.query
    if request.league:
        query = f"{query} ({request.league})"

    logger.info(f"Search request: {query[:80]}...")


    stat_keywords = ["stats", "statistics", "fouls", "points", "performance",
                     "season", "average", "per game", "technical"]
    extract_stats = any(kw in query.lower() for kw in stat_keywords)

    result = _run_adk_search(query, extract_stats=extract_stats)
    logger.info(f"Search result: status={result['status']}, league={result.get('league')}")

    return result


@app.post("/player-stats")
def player_stats(request: PlayerStatsRequest):

    parts = []
    if request.player:
        parts.append(request.player)
    if request.team:
        parts.append(request.team)
    if request.league:
        parts.append(request.league)

    stat_type = request.stat_type or "season"
    parts.append(f"2025-26 {stat_type} statistics basketball")

    query = " ".join(parts)
    logger.info(f"Player stats request: {query}")

    result = _run_adk_search(query, extract_stats=True)
    return result
