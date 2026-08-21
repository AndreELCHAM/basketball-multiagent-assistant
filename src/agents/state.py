

from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):



    messages: Annotated[list, add_messages]

    thread_id: str                   
    conversation_history: list[dict]   

    user_query: str                    
    user_language: str                 

    english_query: str                 
    league_filter: Optional[str]       


    next_agent: str                    
    route_plan: list[str]              
    tool_input: dict                   
    rewritten_queries: dict   

    retrieved_chunks: list[dict]       
    image_paths: list[str]             


    web_search_results: dict           


    mcp_results: dict                


    pending_human_input: Optional[str] 
    human_input_options: list[str]     
    human_input_message: str           


    final_answer: str                  
    response_type: str                 

    iteration_count: int               
