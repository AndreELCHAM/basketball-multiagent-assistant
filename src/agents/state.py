"""
LangGraph state schema for System A.
Defines the shared state passed between supervisor and agent nodes.
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state for the System A LangGraph workflow."""

    # Conversation history (LangGraph message accumulation)
    messages: Annotated[list, add_messages]

    # User input
    user_query: str                    # Original query (any language)
    user_language: str                 # Detected language code: "en", "fr", "es", "ar"

    # Processed query
    english_query: str                 # Translated/normalized English query
    league_filter: Optional[str]       # Extracted league: "FIBA", "NBA", "NCAA", "FIBA_3x3", or None

    # Retrieval results
    retrieved_chunks: list[dict]       # RAG results with text + metadata
    image_paths: list[str]            # Diagram paths from retrieved chunks

    # Output
    final_answer: str                  # Synthesized answer in user_language

    # Routing control
    next_agent: str                    # "rag_agent", "web_agent", "mcp_tools", "__end__"
    iteration_count: int               # Guard against infinite loops
