
import logging

from src.agents.state import AgentState

logger = logging.getLogger(__name__)


def human_input_node(state: AgentState) -> dict:

    pending = state.get("pending_human_input", "")
    message = state.get("human_input_message", "Which league is your question about?")
    options = state.get("human_input_options", ["NBA", "FIBA", "NCAA", "FIBA_3x3"])

    logger.info(f"Human Input Node: type={pending}, options={options}")

    return {
        "final_answer": message,
        "response_type": "league_prompt",
        "human_input_options": options,
        "human_input_message": message,
        "next_agent": "__end__",
    }
