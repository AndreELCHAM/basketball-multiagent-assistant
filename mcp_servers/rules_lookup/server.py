"""
MCP Tool #1: Rules Lookup Server
A deterministic tool for retrieving structured rule text.
"""

import logging
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Tool 1: Rules Lookup")

class LookupRequest(BaseModel):
    rule_id: str
    league: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mcp-rules-lookup"}

@app.post("/lookup")
def lookup_rule(request: LookupRequest):
    """
    Lookup exact rule text by ID.
    Stub implementation.
    """
    logger.info(f"Looking up rule {request.rule_id} for league {request.league}")
    return {
        "rule_id": request.rule_id,
        "league": request.league,
        "text": f"[Stub] Exact rule text for {request.rule_id} would go here.",
        "source": "mcp-rules-lookup"
    }
