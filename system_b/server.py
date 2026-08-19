"""
System B — Game Analysis Agent (Google ADK)
A separate multi-agent system on a different tech stack from System A.
Communicates with System A, MongoDB, and MCP tools via HTTP.
"""

import logging
import os
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MCP_RULES_URL = os.getenv("MCP_RULES_URL", "http://localhost:5001")
MCP_FOUL_URL = os.getenv("MCP_FOUL_URL", "http://localhost:5002")

app = FastAPI(
    title="System B — Game Analysis Agent",
    description="Google ADK-based multi-agent system for basketball game analysis",
    version="1.0.0",
)


# ── Models ────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    query: str
    league: Optional[str] = None
    game_id: Optional[str] = None


class StatsRequest(BaseModel):
    player: Optional[str] = None
    team: Optional[str] = None
    league: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Health check endpoint for Docker orchestration."""
    return {
        "status": "ok",
        "system": "B",
        "framework": "Google ADK",
        "services": {
            "mongodb": MONGODB_URL,
            "mcp_rules": MCP_RULES_URL,
            "mcp_foul": MCP_FOUL_URL,
        },
    }


@app.post("/analyze")
def analyze_game(request: AnalyzeRequest):
    """
    Analyze a game situation using multi-agent reasoning.
    
    Stub — will be implemented with Google ADK agents that:
    - Query MongoDB for game context
    - Call MCP tools for rule lookups and foul calculations
    - Synthesize analysis using an LLM
    """
    logger.info(f"Analyze request: {request.query[:80]}...")
    return {
        "status": "stub",
        "message": "Game analysis endpoint — to be implemented with Google ADK",
        "query": request.query,
        "league": request.league,
    }


@app.post("/stats")
def get_stats(request: StatsRequest):
    """
    Retrieve game/player statistics from MongoDB.
    
    Stub — will query MongoDB for historical game data.
    """
    logger.info(f"Stats request: player={request.player}, team={request.team}")
    return {
        "status": "stub",
        "message": "Stats endpoint — to be implemented with MongoDB queries",
        "player": request.player,
        "team": request.team,
    }
