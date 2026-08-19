"""
Evaluates the final LLM responses for all queries in the test dataset.
Runs the full LangGraph RAG pipeline (System A) on each query and saves the answers.
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR, TEST_DATASET_PATH
from src.agents.graph import run_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def evaluate_llm():
    if not TEST_DATASET_PATH.exists():
        logger.error(f"Test dataset not found at {TEST_DATASET_PATH}")
        sys.exit(1)

    with open(TEST_DATASET_PATH, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    logger.info(f"Running full LLM pipeline on {len(test_data)} test queries...")

    from tabulate import tabulate
    
    output_lines = ["# LLM End-to-End Evaluation\n"]
    
    total_score = 0
    total_keywords = 0
    keywords_found = 0
    retrieval_hits = 0
    
    table_data = []
    details_lines = ["\n## Detailed LLM Responses\n"]
    
    for i, item in enumerate(test_data, 1):
        query = item["query"]
        expected_league = item.get("expected_league", "Unknown")
        gt_keywords = item.get("ground_truth_keywords", [])
        gt_section = item.get("ground_truth_section", "")
        
        logger.info(f"[{i}/{len(test_data)}] Processing: {query}")
        
        try:
            # Run the full RAG graph
            state = run_query(query)
            
            answer = state.get("final_answer", "No answer generated.")
            detected_lang = state.get("user_language", "en")
            retrieved_chunks = state.get("retrieved_chunks", [])
            
            from src.evaluation.metrics import _is_relevant
            
            # Check Retrieval Hit using official metrics
            retrieval_hit = False
            for chunk in retrieved_chunks:
                if _is_relevant(chunk, gt_section, gt_keywords):
                    retrieval_hit = True
                    break
            
            if retrieval_hit:
                retrieval_hits += 1
            
            # Calculate correctness via Keyword Matching
            answer_lower = answer.lower()
            found = [kw for kw in gt_keywords if kw.lower() in answer_lower]
            score = len(found) / len(gt_keywords) if gt_keywords else 0
            
            total_keywords += len(gt_keywords)
            keywords_found += len(found)
            total_score += score
            
            # Print real-time progress to terminal
            print(f"\n[{i}/{len(test_data)}] {query}")
            print(f"  ↳ Hit: {'✅' if retrieval_hit else '❌'} | Score: {score*100:.0f}%")
            print(f"  ↳ Snippet: {answer[:80].replace(chr(10), ' ')}...")
            
            # Add to table
            table_data.append({
                "ID": i,
                "League": expected_league,
                "Query": query[:45] + "..." if len(query) > 45 else query,
                "Chunk Hit": "✅" if retrieval_hit else "❌",
                "Score": f"{score*100:.0f}%",
                "Answer Snippet": answer[:60].replace("\n", " ") + "..."
            })
            
            # Add to details
            details_lines.append(f"### {i}. {query}")
            details_lines.append(f"**Score:** {score*100:.0f}% | **Chunk Hit:** {'✅' if retrieval_hit else '❌'}")
            details_lines.append(f"**Keywords Hit:** {', '.join(found) if found else 'None'} / {', '.join(gt_keywords)}")
            details_lines.append(f"**Full Answer:**\n{answer}\n")
            details_lines.append("---\n")
            
        except Exception as e:
            logger.error(f"Error on query {i}: {e}")
            table_data.append({
                "ID": i,
                "League": expected_league,
                "Query": query[:45] + "..." if len(query) > 45 else query,
                "Chunk Hit": "ERROR",
                "Score": "ERROR",
                "Answer Snippet": str(e)[:60]
            })
            details_lines.append(f"### {i}. {query}")
            details_lines.append(f"**Error:** {str(e)}\n")
            details_lines.append("---\n")

    avg_score = (total_score / len(test_data)) * 100
    overall_kw_hit = (keywords_found / total_keywords) * 100 if total_keywords else 0
    retrieval_hit_rate = (retrieval_hits / len(test_data)) * 100
    
    # Build Top Summary
    output_lines.append(f"**Overall Average Score:** {avg_score:.1f}%")
    output_lines.append(f"**Total Keywords Hit:** {overall_kw_hit:.1f}% ({keywords_found}/{total_keywords})")
    output_lines.append(f"**Retrieval Hit Rate:** {retrieval_hit_rate:.1f}% ({retrieval_hits}/{len(test_data)})\n")
    
    # Add Table
    output_lines.append(tabulate(table_data, headers="keys", tablefmt="github"))
    output_lines.append("\n")
    
    # Add Details
    output_lines.extend(details_lines)

    results_path = DATA_DIR / "llm_evaluation_results.md"
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    logger.info(f"Evaluation complete! Results saved to {results_path}")


if __name__ == "__main__":
    evaluate_llm()
