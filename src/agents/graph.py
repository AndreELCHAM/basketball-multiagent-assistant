"""
LangGraph workflow assembly for System A.
Builds the supervisor → agent graph with configurable routing modes.
"""

import logging

from langgraph.graph import StateGraph, END

from src.agents.state import AgentState
from src.agents.supervisor import supervisor_node
from src.agents.rag_agent import rag_agent_node

logger = logging.getLogger(__name__)


def _route_after_supervisor(state: AgentState) -> str:
    """Conditional edge: route based on supervisor's next_agent decision."""
    next_agent = state.get("next_agent", "rag_agent")

    if next_agent == "__end__":
        return END

    # Safety: check iteration count
    if state.get("iteration_count", 0) >= 5:
        logger.warning("Max iterations reached, forcing end")
        return END

    if next_agent == "rag_agent":
        return "rag_agent"

    # Stubs for future agents — fall back to rag_agent for now
    if next_agent in ("web_agent", "mcp_tools"):
        logger.info(f"  Agent '{next_agent}' not yet implemented, falling back to rag_agent")
        return "rag_agent"

    return "rag_agent"


def build_graph() -> StateGraph:
    """
    Build and compile the System A LangGraph workflow.

    Graph structure:
        START → supervisor → rag_agent → END
                          → (web_agent stub) → END
                          → (mcp_tools stub) → END
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("rag_agent", rag_agent_node)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Conditional routing from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "rag_agent": "rag_agent",
            END: END,
        },
    )

    # RAG agent always ends
    workflow.add_edge("rag_agent", END)

    # Compile with recursion limit
    graph = workflow.compile()

    logger.info("System A graph compiled successfully")
    return graph


def run_query(
    query: str,
    league: str = None,
) -> dict:
    """
    Run a single query through the System A pipeline.

    Args:
        query: user query in any supported language
        league: optional league override (bypasses extraction)

    Returns:
        Final state dict with keys: final_answer, retrieved_chunks, image_paths, etc.
    """
    graph = build_graph()

    initial_state = {
        "messages": [],
        "user_query": query,
        "user_language": "",
        "english_query": "",
        "league_filter": league,
        "retrieved_chunks": [],
        "image_paths": [],
        "final_answer": "",
        "next_agent": "",
        "iteration_count": 0,
    }

    # Run the graph
    config = {"recursion_limit": 5}
    final_state = graph.invoke(initial_state, config=config)

    return final_state
