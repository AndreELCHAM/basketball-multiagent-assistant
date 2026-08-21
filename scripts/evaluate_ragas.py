

import json
import logging
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR, TEST_DATASET_PATH, LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL
from src.agents.graph import run_query

from datasets import Dataset


import sys
import types
dummy_vertexai = types.ModuleType("langchain_community.chat_models.vertexai")
dummy_vertexai.ChatVertexAI = type("ChatVertexAI", (object,), {})
sys.modules["langchain_community.chat_models.vertexai"] = dummy_vertexai


from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, answer_correctness, context_precision, context_recall
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def evaluate_with_ragas():
    if not TEST_DATASET_PATH.exists():
        logger.error(f"Test dataset not found at {TEST_DATASET_PATH}")
        sys.exit(1)

    with open(TEST_DATASET_PATH, "r", encoding="utf-8") as f:
        test_data = json.load(f)



    logger.info(f"Running full LLM pipeline and Ragas evaluation on {len(test_data)} test queries...")

    # Setup Ragas LLM and Embedder
    eval_llm = ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        default_headers={"HTTP-Referer": "http://localhost", "X-Title": "basketball-multiagent-assistant"},
        temperature=0.0
    )
    

    eval_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

    data_samples = {
        "user_input": [],
        "response": [],
        "retrieved_contexts": [],
        "reference": [],
    }

    for i, item in enumerate(test_data, 1):
        query = item["query"]
        logger.info(f"[{i}/{len(test_data)}] Processing query: {query}")
        
        try:
            # Run the full RAG graph
            state = run_query(query)
            
            answer = state.get("final_answer", "No answer generated.")
            
            # Clean <thinking> blocks so Ragas doesn't penalize Answer Relevancy for "rambling"
            import re
            clean_answer = re.sub(r"<thinking>.*?</thinking>", "", answer, flags=re.DOTALL).strip()
            
            retrieved_chunks = state.get("retrieved_chunks", [])
            contexts = [chunk.get("text", "") for chunk in retrieved_chunks]
            
            ground_truth = item.get("ground_truth_answer", "")
            
            data_samples["user_input"].append(query)
            data_samples["response"].append(clean_answer)
            data_samples["retrieved_contexts"].append(contexts)
            data_samples["reference"].append(ground_truth)
            
        except Exception as e:
            logger.error(f"Error on query {i}: {e}")
            data_samples["user_input"].append(query)
            data_samples["response"].append("ERROR: " + str(e))
            data_samples["retrieved_contexts"].append([""])
            data_samples["reference"].append("")

    dataset = Dataset.from_dict(data_samples)

    # Run Ragas Evaluation
    logger.info("Running Ragas metrics (Faithfulness, Answer Relevancy, Answer Correctness, Context Precision, Context Recall)...")
    try:
        results = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, answer_correctness, context_precision, context_recall],
            llm=eval_llm,
            embeddings=eval_embeddings
        )
        
        results_df = results.to_pandas()
        
        # Cleanly print results
        from tabulate import tabulate
        
        # Print Overall Metrics
        print("\n" + "="*50)
        print("RAGAS EVALUATION RESULTS")
        print("="*50)
        
        overall_scores = []
        if 'faithfulness' in results_df.columns:
            overall_scores.append(f"Faithfulness: {results_df['faithfulness'].mean():.4f}")
        if 'answer_relevancy' in results_df.columns:
            overall_scores.append(f"Answer Relevancy: {results_df['answer_relevancy'].mean():.4f}")
        if 'answer_correctness' in results_df.columns:
            overall_scores.append(f"Answer Correctness: {results_df['answer_correctness'].mean():.4f}")
        if 'context_precision' in results_df.columns:
            overall_scores.append(f"Context Precision: {results_df['context_precision'].mean():.4f}")
        if 'context_recall' in results_df.columns:
            overall_scores.append(f"Context Recall: {results_df['context_recall'].mean():.4f}")
            
        for score in overall_scores:
            print(score)
        print("="*50 + "\n")
        

        display_df = results_df.copy()
        

        if 'user_input' in display_df.columns:
            display_df['user_input'] = display_df['user_input'].apply(lambda x: str(x)[:40] + '...' if len(str(x)) > 40 else str(x))
        if 'response' in display_df.columns:
            display_df['response'] = display_df['response'].apply(lambda x: str(x)[:40] + '...' if len(str(x)) > 40 else str(x))
        
        columns_to_show = ['user_input', 'response']
        if 'faithfulness' in display_df.columns:
            display_df['faithfulness'] = display_df['faithfulness'].round(4)
            columns_to_show.append('faithfulness')
        if 'answer_relevancy' in display_df.columns:
            display_df['answer_relevancy'] = display_df['answer_relevancy'].round(4)
            columns_to_show.append('answer_relevancy')
        if 'answer_correctness' in display_df.columns:
            display_df['answer_correctness'] = display_df['answer_correctness'].round(4)
            columns_to_show.append('answer_correctness')
        if 'context_precision' in display_df.columns:
            display_df['context_precision'] = display_df['context_precision'].round(4)
            columns_to_show.append('context_precision')
        if 'context_recall' in display_df.columns:
            display_df['context_recall'] = display_df['context_recall'].round(4)
            columns_to_show.append('context_recall')
            
        print(tabulate(display_df[columns_to_show], headers='keys', tablefmt='github', showindex=False))
        print("\n")
        
        # Save to markdown
        results_path = DATA_DIR / "ragas_evaluation_results.md"
        with open(results_path, "w", encoding="utf-8") as f:
            f.write("# Ragas Evaluation Results\n\n")
            f.write("## Overall Metrics\n")
            for score in overall_scores:
                f.write(f"- **{score}**\n")
            f.write("\n## Detailed Results\n")
            f.write(tabulate(display_df[columns_to_show], headers='keys', tablefmt='github', showindex=False))
            f.write("\n\n")
            
            # Full details
            f.write("## Full QA Details\n")
            for idx, row in results_df.iterrows():
                f.write(f"### Q: {row.get('user_input', 'N/A')}\n")
                if 'faithfulness' in row and not os.environ.get("PANDAS_IS_NA", False):
                    f.write(f"**Faithfulness:** {row.get('faithfulness', 'N/A')}\n")
                if 'answer_relevancy' in row:
                    f.write(f"**Answer Relevancy:** {row.get('answer_relevancy', 'N/A')}\n")
                if 'answer_correctness' in row:
                    f.write(f"**Answer Correctness:** {row.get('answer_correctness', 'N/A')}\n")
                if 'context_precision' in row:
                    f.write(f"**Context Precision:** {row.get('context_precision', 'N/A')}\n")
                if 'context_recall' in row:
                    f.write(f"**Context Recall:** {row.get('context_recall', 'N/A')}\n")
                f.write(f"**Answer:**\n{row.get('response', 'N/A')}\n")
                f.write(f"---\n")

        logger.info(f"Ragas evaluation complete! Results saved to {results_path}")

    except Exception as e:
        logger.error(f"Ragas evaluation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    evaluate_with_ragas()
