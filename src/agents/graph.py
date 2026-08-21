

import logging
import uuid

from langgraph.graph import StateGraph, END

from src.agents.state import AgentState
from src.agents.supervisor import supervisor_node
from src.agents.rag_agent import rag_agent_node
from src.agents.web_agent import web_agent_node
from src.agents.mcp_agent import mcp_suspension_node, mcp_performance_node
from src.agents.human_input import human_input_node

logger = logging.getLogger(__name__)

MAX_ITERATIONS_PER_QUERY = 8


def _route_after_supervisor(state: AgentState) -> str:
    next_agent = state.get("next_agent", "rag_agent")

    if next_agent == "__end__":
        return END


    if state.get("iteration_count", 0) >= MAX_ITERATIONS_PER_QUERY:
        logger.warning("Max iterations per query reached, forcing end")
        return END

    valid_agents = {"rag_agent", "web_agent", "mcp_suspension", "mcp_performance", "human_input"}
    if next_agent in valid_agents:
        return next_agent

    logger.warning(f"Unknown agent '{next_agent}', falling back to rag_agent")
    return "rag_agent"


def _route_after_web_agent(state: AgentState) -> str:

    next_agent = state.get("next_agent", "__end__")

    if next_agent == "supervisor":
        if state.get("iteration_count", 0) >= MAX_ITERATIONS_PER_QUERY:
            logger.warning("Max iterations reached after web_agent, forcing end")
            return END
        return "supervisor"

    return END


def build_graph() -> StateGraph:

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("rag_agent", rag_agent_node)
    workflow.add_node("web_agent", web_agent_node)
    workflow.add_node("mcp_suspension", mcp_suspension_node)
    workflow.add_node("mcp_performance", mcp_performance_node)
    workflow.add_node("human_input", human_input_node)

    workflow.set_entry_point("supervisor")


    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "rag_agent": "rag_agent",
            "web_agent": "web_agent",
            "mcp_suspension": "mcp_suspension",
            "mcp_performance": "mcp_performance",
            "human_input": "human_input",
            END: END,
        },
    )


    workflow.add_conditional_edges(
        "web_agent",
        _route_after_web_agent,
        {
            "supervisor": "supervisor",
            END: END,
        },
    )

    workflow.add_edge("rag_agent", END)
    workflow.add_edge("mcp_suspension", END)
    workflow.add_edge("mcp_performance", END)
    workflow.add_edge("human_input", END)
    graph = workflow.compile()

    logger.info("System A graph compiled successfully (full multi-agent)")
    return graph


def run_query(
    query: str,
    league: str = None,
    thread_id: str = None,
    conversation_history: list = None,
) -> dict:

    graph = build_graph()

    if not thread_id:
        thread_id = str(uuid.uuid4())

    initial_state = {
        "messages": [],
        "thread_id": thread_id,
        "conversation_history": conversation_history or [],
        "user_query": query,
        "user_language": "",
        "english_query": "",
        "league_filter": league,
        "retrieved_chunks": [],
        "image_paths": [],
        "web_search_results": {},
        "mcp_results": {},
        "final_answer": "",
        "next_agent": "",
        "route_plan": [],
        "tool_input": {},
        "rewritten_queries": {},
        "pending_human_input": None,
        "human_input_options": [],
        "human_input_message": "",
        "response_type": "answer",
        "iteration_count": 0,  # Fresh per query
    }

    # Run the graph
    config = {"recursion_limit": MAX_ITERATIONS_PER_QUERY + 2}
    final_state = graph.invoke(initial_state, config=config)

    return final_state
