"""
RAG Agent node for System A.
Retrieves relevant rulebook chunks and synthesizes a grounded,
multimodal-aware answer, translating back to the user's language.
Supports multi-league comparisons (split queries across leagues).
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

    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def _format_context(chunks: list[dict]) -> str:

    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        league = meta.get("league", "Unknown")
        section = meta.get("article_or_section", "Unknown")
        text = chunk.get("text", "")
        score = chunk.get("score", 0.0)

        header = f"[Source {i}] {league} — {section} (relevance: {score:.3f})"
        parts.append(f"{header}\n{text}")


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
    is_comparison: bool = False,
) -> str:


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

    comparison_instruction = ""
    if is_comparison:
        comparison_instruction = (
            "\n\nThis is a CROSS-LEAGUE COMPARISON query. The sources come from different "
            "league rulebooks. Structure your answer to clearly compare and contrast the rules "
            "between leagues. Use a comparison format (e.g., side-by-side or separate sections "
            "for each league) to highlight similarities and differences."
        )

    system_prompt = (
        "You are an expert basketball rules assistant. Your job is to answer the user's question "
        "using ONLY the provided rulebook sources. Do not use outside knowledge.\n\n"
        "You must follow these strict rules:\n"
        "1. CHAIN OF THOUGHT: You must first write a <thinking> block to analyze the rules, "
        "cross-reference the retrieved sources, and build a logical argument before outputting your final answer.\n"
        "2. CITATIONS: Every single claim in your final answer MUST be supported by an inline citation "
        "matching the source index, e.g., [Source 1] or [Source 2].\n"
        "3. NO HALLUCINATIONS: If the provided sources do not contain enough information to "
        "fully answer the question, you must explicitly say so.\n"
        f"{comparison_instruction}"
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
    answer = response.choices[0].message.content.strip()
    
    # Strip the <thinking> block from the final output
    import re
    answer = re.sub(r"<thinking>.*?</thinking>\s*", "", answer, flags=re.DOTALL)
    
    return answer


def rag_agent_node(state: AgentState) -> dict:

    english_query = state["english_query"]
    league_filter = state.get("league_filter")
    user_language = state.get("user_language", "en")
    rewritten_queries = state.get("rewritten_queries", {})

    logger.info(f"RAG Agent: query='{english_query[:80]}...', league={league_filter}")

    is_comparison = league_filter == "MULTI"
    all_results = []

    if is_comparison:

        league_queries = {
            k: v for k, v in rewritten_queries.items()
            if k.startswith("rag_agent_")
        }

        if not league_queries:
            league_queries = {
                "rag_agent_NBA": english_query,
                "rag_agent_FIBA": english_query,
            }

        for key, query_text in league_queries.items():

            league_name = key.replace("rag_agent_", "").upper()
            logger.info(f"  Comparison query for {league_name}: '{query_text[:60]}...'")

            results, latency = retrieve(
                query=query_text,
                collection_name=RETRIEVAL_COLLECTION,
                pipeline=RETRIEVAL_PIPELINE,
                top_k=RETRIEVAL_TOP_K,
                league_filter=league_name,
            )
            logger.info(f"    Retrieved {len(results)} chunks for {league_name} in {latency:.1f}ms")
            all_results.extend(results)
    else:

        rag_query = rewritten_queries.get("rag_agent", english_query)
        results, latency = retrieve(
            query=rag_query,
            collection_name=RETRIEVAL_COLLECTION,
            pipeline=RETRIEVAL_PIPELINE,
            top_k=RETRIEVAL_TOP_K,
            league_filter=league_filter,
        )
        logger.info(f"  Retrieved {len(results)} chunks in {latency:.1f}ms")
        all_results = results

    # Collect image paths
    image_paths = []
    for r in all_results:
        meta = r.get("metadata", {})
        if meta.get("has_image") and meta.get("image_path"):
            image_paths.append(meta["image_path"])

    has_diagrams = len(image_paths) > 0
    logger.info(f"  Found {len(image_paths)} diagram references")

    # Synthesize answer
    if all_results:
        context = _format_context(all_results)
        client = _get_llm_client()
        answer = _synthesize_answer(
            client, english_query, context, user_language,
            has_diagrams, is_comparison
        )
    else:
        answer = (
            "I could not find relevant information in the basketball rulebooks to answer "
            "your question. Please try rephrasing or specifying the league (FIBA, NBA, NCAA, 3x3)."
        )

    logger.info(f"  Answer generated ({len(answer)} chars)")

    return {
        "retrieved_chunks": all_results,
        "image_paths": image_paths,
        "final_answer": answer,
        "next_agent": "__end__",
        "response_type": "answer",
    }
