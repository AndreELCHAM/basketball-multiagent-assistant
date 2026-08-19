"""
FastAPI HTTP API layer for System A.
Wraps the existing LangGraph RAG pipeline with REST endpoints
so the frontend and other services can communicate via HTTP.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.graph import run_query
from src.config import SYSTEM_B_URL, MCP_RULES_URL, MCP_FOUL_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="System A — Basketball Rules RAG",
    description="LangGraph-powered RAG pipeline for basketball rulebook Q&A",
    version="1.0.0",
)

# Allow frontend (and any origin in dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    league: Optional[str] = None


class ChunkResponse(BaseModel):
    text: str
    metadata: dict
    score: float


class QueryResponse(BaseModel):
    answer: str
    language: str
    league_filter: Optional[str]
    chunks: list[ChunkResponse]
    image_paths: list[str]


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """Health check endpoint for Docker container orchestration."""
    return {
        "status": "ok",
        "system": "A",
        "framework": "LangGraph",
        "services": {
            "system_b": SYSTEM_B_URL,
            "mcp_rules": MCP_RULES_URL,
            "mcp_foul": MCP_FOUL_URL,
        },
    }


@app.post("/api/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """
    Main query endpoint. Runs the full LangGraph RAG pipeline.

    Accepts a basketball rules question (in any language) and returns
    a grounded answer with source chunks and diagram references.
    """
    logger.info(f"API query: '{request.query[:80]}...' league={request.league}")

    state = run_query(request.query, league=request.league)

    chunks = [
        ChunkResponse(
            text=c.get("text", ""),
            metadata=c.get("metadata", {}),
            score=c.get("score", 0.0),
        )
        for c in state.get("retrieved_chunks", [])
    ]

    return QueryResponse(
        answer=state.get("final_answer", "No answer generated."),
        language=state.get("user_language", "en"),
        league_filter=state.get("league_filter"),
        chunks=chunks,
        image_paths=state.get("image_paths", []),
    )
