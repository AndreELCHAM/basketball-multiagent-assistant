"""
RAG Agent node for System A.
Retrieves relevant rulebook chunks and synthesizes a grounded,
multimodal-aware answer, translating back to the user's language.
"""

import logging

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    RETRIEVAL_PIPELINE,
    RETRIEVAL_COLLECTION,
    RETRIEVAL_TOP_K,
)
from src.agents.state import AgentState
from src.retrieval.retriever import retrieve

logger = logging.getLogger(__name__)


def _get_llm_client() -> OpenAI:
    """Create OpenRouter client."""
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def _format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        league = meta.get("league", "Unknown")
        section = meta.get("article_or_section", "Unknown")
        text = chunk.get("text", "")
        score = chunk.get("score", 0.0)

        header = f"[Source {i}] {league} — {section} (relevance: {score:.3f})"
        parts.append(f"{header}\n{text}")

        # Include image caption if available
        if meta.get("image_caption"):
            parts.append(f"[Diagram for Source {i}]: {meta['image_caption']}")

    return "\n\n---\n\n".join(parts)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
)
def _synthesize_answer(
    client: OpenAI,
    english_query: str,
    context: str,
    user_language: str,
    has_diagrams: bool,
) -> str:
    """Call LLM to synthesize a grounded answer from retrieved context."""

    language_instruction = ""
    if user_language != "en":
        lang_names = {"fr": "French", "es": "Spanish", "ar": "Arabic"}
        lang_name = lang_names.get(user_language, user_language)
        language_instruction = (
            f"\n\nIMPORTANT: The user's language is {lang_name}. "
            f"You MUST write your final answer in {lang_name}."
        )

    diagram_instruction = ""
    if has_diagrams:
        diagram_instruction = (
            "\n\nSome sources include diagram descriptions. Reference these visual "
            "elements in your answer when relevant (e.g., 'As shown in the court diagram...')."
        )

    system_prompt = (
        "You are an expert basketball rules assistant. Answer the user's question "
        "using ONLY the provided rulebook sources. Be precise, cite the specific "
        "rule/article when possible, and ground every claim in the source material.\n\n"
        "If the sources do not contain enough information to fully answer the question, "
        "say so explicitly — do not fabricate rules."
        f"{diagram_instruction}"
        f"{language_instruction}"
    )

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Question: {english_query}\n\n"
                    f"Retrieved Rulebook Sources:\n\n{context}"
                ),
            },
        ],
        max_tokens=2048,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def rag_agent_node(state: AgentState) -> dict:
    """
    RAG Agent node for LangGraph.

    1. Retrieves relevant chunks using the configured pipeline.
    2. Collects image paths from retrieved metadata.
    3. Synthesizes a grounded answer via LLM.
    4. Translates back to user_language if needed.
    """
    english_query = state["english_query"]
    league_filter = state.get("league_filter")
    user_language = state.get("user_language", "en")

    logger.info(f"RAG Agent: query='{english_query[:80]}...', league={league_filter}")

    # Step 1: Retrieve
    results, latency = retrieve(
        query=english_query,
        collection_name=RETRIEVAL_COLLECTION,
        pipeline=RETRIEVAL_PIPELINE,
        top_k=RETRIEVAL_TOP_K,
        league_filter=league_filter,
    )
    logger.info(f"  Retrieved {len(results)} chunks in {latency:.1f}ms")

    # Step 2: Collect image paths
    image_paths = []
    for r in results:
        meta = r.get("metadata", {})
        if meta.get("has_image") and meta.get("image_path"):
            image_paths.append(meta["image_path"])

    has_diagrams = len(image_paths) > 0
    logger.info(f"  Found {len(image_paths)} diagram references")

    # Step 3: Synthesize answer
    if results:
        context = _format_context(results)
        client = _get_llm_client()
        answer = _synthesize_answer(client, english_query, context, user_language, has_diagrams)
    else:
        answer = (
            "I could not find relevant information in the basketball rulebooks to answer "
            "your question. Please try rephrasing or specifying the league (FIBA, NBA, NCAA, 3x3)."
        )

    logger.info(f"  Answer generated ({len(answer)} chars)")

    return {
        "retrieved_chunks": results,
        "image_paths": image_paths,
        "final_answer": answer,
        "next_agent": "__end__",
    }
