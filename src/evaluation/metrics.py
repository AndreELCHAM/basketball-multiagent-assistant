
import math
from typing import Optional


def hit_rate_at_k(
    results: list[dict],
    ground_truth_section: str,
    ground_truth_keywords: list[str],
    k: int = 5,
) -> float:

    top_results = results[:k]

    for result in top_results:
        if _is_relevant(result, ground_truth_section, ground_truth_keywords):
            return 1.0
    return 0.0


def precision_at_k(
    results: list[dict],
    ground_truth_section: str,
    ground_truth_keywords: list[str],
    k: int = 5,
) -> float:

    top_results = results[:k]
    if not top_results:
        return 0.0

    relevant_count = sum(
        1 for r in top_results
        if _is_relevant(r, ground_truth_section, ground_truth_keywords)
    )
    return relevant_count / k


def recall_at_k(
    results: list[dict],
    ground_truth_section: str,
    ground_truth_keywords: list[str],
    k: int = 5,
    total_relevant: int = 1,
) -> float:

    all_relevant = sum(
        1 for r in results
        if _is_relevant(r, ground_truth_section, ground_truth_keywords)
    )
    total = max(all_relevant, total_relevant)

    top_results = results[:k]
    found_relevant = sum(
        1 for r in top_results
        if _is_relevant(r, ground_truth_section, ground_truth_keywords)
    )

    return found_relevant / total if total > 0 else 0.0


def ndcg_at_k(
    results: list[dict],
    ground_truth_section: str,
    ground_truth_keywords: list[str],
    k: int = 5,
) -> float:
    
    top_results = results[:k]

    # Build binary relevance vector
    relevance = [
        1.0 if _is_relevant(r, ground_truth_section, ground_truth_keywords) else 0.0
        for r in top_results
    ]

    # DCG: actual ranking
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(relevance))

    # IDCG: ideal ranking (all 1s first)
    ideal_relevance = sorted(relevance, reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_relevance))

    if idcg == 0:
        return 0.0

    return dcg / idcg


def reciprocal_rank(
    results: list[dict],
    ground_truth_section: str,
    ground_truth_keywords: list[str],
) -> float:

    for i, result in enumerate(results):
        if _is_relevant(result, ground_truth_section, ground_truth_keywords):
            return 1.0 / (i + 1)
    return 0.0


def _is_relevant(
    result: dict,
    ground_truth_section: str,
    ground_truth_keywords: list[str],
) -> bool:

    text = result.get("text", "").lower()
    metadata = result.get("metadata", {})
    section = metadata.get("article_or_section", "").lower()

    # Check 1: section name match
    gt_section_lower = ground_truth_section.lower()
    if gt_section_lower and gt_section_lower in section:
        return True
    if gt_section_lower and section and section in gt_section_lower:
        return True

    # Check 2: keyword overlap in text
    if ground_truth_keywords:
        matched = sum(1 for kw in ground_truth_keywords if kw.lower() in text)
        threshold = max(1, len(ground_truth_keywords) // 2)
        if matched >= threshold:
            return True

    return False


def evaluate_queries(
    query_results: list[dict],
    k_values: Optional[list[int]] = None,
) -> dict:

    if k_values is None:
        k_values = [3, 5]

    per_query = []
    total_latency = 0.0
    hit_counts = {k: 0 for k in k_values}
    precision_sums = {k: 0.0 for k in k_values}
    recall_sums = {k: 0.0 for k in k_values}
    ndcg_sums = {k: 0.0 for k in k_values}
    total_rr = 0.0
    n = len(query_results)

    for qr in query_results:
        results = qr["results"]
        gt_section = qr["ground_truth_section"]
        gt_keywords = qr["ground_truth_keywords"]
        latency = qr["latency_ms"]

        rr = reciprocal_rank(results, gt_section, gt_keywords)
        query_metrics = {}
        for k in k_values:
            h = hit_rate_at_k(results, gt_section, gt_keywords, k)
            p = precision_at_k(results, gt_section, gt_keywords, k)
            r = recall_at_k(results, gt_section, gt_keywords, k)
            nd = ndcg_at_k(results, gt_section, gt_keywords, k)

            query_metrics[f"hit@{k}"] = h
            query_metrics[f"p@{k}"] = p
            query_metrics[f"r@{k}"] = r
            query_metrics[f"ndcg@{k}"] = nd

            hit_counts[k] += h
            precision_sums[k] += p
            recall_sums[k] += r
            ndcg_sums[k] += nd

        per_query.append({
            "query": qr["query"],
            "rr": rr,
            **query_metrics,
            "latency_ms": latency,
        })

        total_rr += rr
        total_latency += latency

    metrics = {
        "mrr": total_rr / n if n > 0 else 0.0,
        "avg_latency_ms": total_latency / n if n > 0 else 0.0,
        "per_query": per_query,
    }

    for k in k_values:
        metrics[f"hit_rate_at_{k}"] = hit_counts[k] / n if n > 0 else 0.0
        metrics[f"precision_at_{k}"] = precision_sums[k] / n if n > 0 else 0.0
        metrics[f"recall_at_{k}"] = recall_sums[k] / n if n > 0 else 0.0
        metrics[f"ndcg_at_{k}"] = ndcg_sums[k] / n if n > 0 else 0.0

    return metrics

