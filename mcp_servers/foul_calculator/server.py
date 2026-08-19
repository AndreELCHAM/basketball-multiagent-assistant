"""
MCP Tool #2: Foul Calculator
A deterministic tool for calculating foul limits and penalty situations.
"""

import logging
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Tool 2: Foul Calculator")

class CalculateRequest(BaseModel):
    fouls: int
    league: str
    period: Optional[int] = None

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mcp-foul-calculator"}

@app.post("/calculate")
def calculate_fouls(request: CalculateRequest):
    """
    Calculate penalty progression based on foul count.
    Stub implementation.
    """
    logger.info(f"Calculating for {request.fouls} fouls in league {request.league}")
    return {
        "fouls": request.fouls,
        "league": request.league,
        "foul_out_status": False,
        "penalty_status": "Stub calculation result",
        "source": "mcp-foul-calculator"
    }
