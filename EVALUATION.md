# Evaluation Report

## 1. Test Set

The evaluation uses a curated master dataset of **30 queries** covering diverse question types across all four supported leagues.

**Dataset:** `data/test_benchmark_dataset_master.json`

### Query Type Distribution

| Category | Count | Description |
|----------|-------|-------------|
| Standard RAG | 8 | Direct rules questions with clear league context |
| Visual/Diagram | 4 | Questions about court dimensions, markings, and referee signals |
| Multilingual | 6 | Queries in French (3) and Spanish (3) |
| Cross-Document | 3 | Comparative questions requiring multiple rulebook sources |
| Scenario-Based | 6 | Complex game situations requiring rule interpretation |
| Slang/Informal | 3 | Casual language queries testing robustness |

All queries include ground truth answers, expected source sections, and relevant keywords for automated evaluation.

---

## 2. Retrieval Metrics

We benchmarked **16 configurations** (4 embedding collections × 4 retrieval pipelines) across 3 test datasets (18, 20, and 15 queries).

### Dataset 1 (18 queries)

| Collection | Pipeline | P@5 | R@5 | Hit@3 | Hit@5 | MRR | NDCG@5 | Latency (ms) |
|---|---|---|---|---|---|---|---|---|
| markdown_bge_m3 | dense | 0.678 | 0.833 | 0.833 | 0.833 | 0.769 | 0.786 | 2990 |
| markdown_bge_m3 | hybrid | 0.667 | 0.833 | 0.778 | 0.833 | 0.792 | 0.790 | 64 |
| markdown_bge_m3 | rerank | 0.767 | 0.889 | 0.889 | 0.889 | 0.889 | 0.884 | 2160 |
| markdown_bge_m3 | hybrid_rerank | 0.778 | 0.889 | 0.889 | 0.889 | 0.861 | 0.864 | 1146 |
| markdown_mpnet | dense | 0.667 | 0.944 | 0.889 | 0.944 | 0.835 | 0.840 | 557 |
| markdown_mpnet | hybrid | 0.756 | 0.889 | 0.889 | 0.889 | 0.833 | 0.843 | 155 |
| markdown_mpnet | rerank | 0.800 | 0.889 | 0.889 | 0.889 | 0.889 | 0.884 | 1175 |
| markdown_mpnet | hybrid_rerank | **0.811** | 0.889 | 0.889 | 0.889 | **0.889** | **0.885** | 1573 |
| recursive_bge_m3 | dense | 0.644 | 0.889 | 0.778 | 0.889 | 0.750 | 0.789 | 56 |
| recursive_bge_m3 | hybrid | 0.667 | 0.833 | 0.833 | 0.833 | 0.833 | 0.825 | 98 |
| recursive_bge_m3 | rerank | 0.778 | 0.889 | 0.889 | 0.889 | 0.889 | 0.873 | 1852 |
| recursive_bge_m3 | hybrid_rerank | 0.778 | 0.889 | 0.833 | 0.889 | 0.847 | 0.849 | 1932 |
| recursive_mpnet | dense | 0.644 | 0.889 | 0.889 | 0.889 | 0.889 | 0.862 | 26 |
| recursive_mpnet | hybrid | 0.778 | 0.889 | 0.889 | 0.889 | 0.889 | 0.871 | 180 |
| recursive_mpnet | rerank | 0.789 | 0.889 | 0.889 | 0.889 | 0.889 | 0.879 | 1589 |
| recursive_mpnet | hybrid_rerank | 0.822 | 0.889 | 0.889 | 0.889 | 0.889 | 0.881 | 1720 |

### Dataset 2 (20 queries)

| Collection | Pipeline | P@5 | R@5 | Hit@3 | Hit@5 | MRR | NDCG@5 | Latency (ms) |
|---|---|---|---|---|---|---|---|---|
| markdown_bge_m3 | dense | 0.580 | 0.850 | 0.800 | 0.850 | 0.704 | 0.733 | 926 |
| markdown_bge_m3 | hybrid | 0.620 | 0.900 | 0.750 | 0.900 | 0.738 | 0.772 | 60 |
| markdown_bge_m3 | rerank | 0.730 | 1.000 | 1.000 | 1.000 | 0.917 | 0.923 | 1480 |
| markdown_bge_m3 | hybrid_rerank | 0.720 | **1.000** | **1.000** | **1.000** | **0.925** | **0.929** | 1244 |
| markdown_mpnet | dense | 0.620 | 0.950 | 0.950 | 0.950 | 0.867 | 0.873 | 365 |
| markdown_mpnet | hybrid | 0.660 | 0.950 | 0.950 | 0.950 | 0.925 | 0.904 | 147 |
| markdown_mpnet | rerank | 0.650 | 1.000 | 0.950 | 1.000 | 0.879 | 0.896 | 1364 |
| markdown_mpnet | hybrid_rerank | **0.690** | **1.000** | 0.950 | **1.000** | 0.887 | 0.907 | 1904 |
| recursive_bge_m3 | dense | 0.470 | 0.800 | 0.800 | 0.800 | 0.683 | 0.704 | 60 |
| recursive_bge_m3 | hybrid | 0.560 | 0.850 | 0.800 | 0.850 | 0.738 | 0.740 | 101 |
| recursive_bge_m3 | rerank | 0.620 | 0.950 | 0.900 | 0.950 | 0.818 | 0.828 | 2174 |
| recursive_bge_m3 | hybrid_rerank | 0.640 | 0.950 | 0.900 | 0.950 | 0.835 | 0.851 | 2549 |
| recursive_mpnet | dense | 0.570 | 0.900 | 0.900 | 0.900 | 0.867 | 0.844 | 31 |
| recursive_mpnet | hybrid | 0.630 | 0.900 | 0.900 | 0.900 | 0.875 | 0.863 | 184 |
| recursive_mpnet | rerank | 0.590 | 0.950 | 0.900 | 0.950 | 0.785 | 0.816 | 1856 |
| recursive_mpnet | hybrid_rerank | 0.640 | 0.900 | 0.900 | 0.900 | 0.817 | 0.839 | 1890 |

### Dataset 3 (15 queries — Situational/Complex)

| Collection | Pipeline | P@5 | R@5 | Hit@3 | Hit@5 | MRR | NDCG@5 | Latency (ms) |
|---|---|---|---|---|---|---|---|---|
| markdown_bge_m3 | dense | 0.320 | 0.600 | 0.600 | 0.600 | 0.456 | 0.490 | 1060 |
| markdown_bge_m3 | hybrid | 0.307 | 0.733 | 0.667 | 0.733 | 0.539 | 0.566 | 64 |
| markdown_bge_m3 | rerank | 0.387 | 0.800 | 0.733 | 0.800 | 0.713 | 0.724 | 1684 |
| markdown_bge_m3 | hybrid_rerank | 0.413 | 0.800 | 0.800 | 0.800 | 0.722 | 0.723 | 1226 |
| markdown_mpnet | dense | 0.387 | 0.733 | 0.533 | 0.733 | 0.543 | 0.583 | 547 |
| markdown_mpnet | hybrid | 0.413 | 0.867 | 0.800 | 0.867 | 0.661 | 0.685 | 151 |
| markdown_mpnet | rerank | 0.400 | 0.800 | 0.800 | 0.800 | 0.722 | 0.721 | 1166 |
| markdown_mpnet | hybrid_rerank | **0.427** | 0.800 | **0.800** | 0.800 | **0.756** | **0.757** | 1429 |
| recursive_bge_m3 | dense | 0.267 | 0.733 | 0.667 | 0.733 | 0.517 | 0.568 | 51 |
| recursive_bge_m3 | hybrid | 0.347 | 0.800 | 0.667 | 0.800 | 0.556 | 0.615 | 104 |
| recursive_bge_m3 | rerank | 0.400 | 0.733 | 0.733 | 0.733 | 0.667 | 0.670 | 1439 |
| recursive_bge_m3 | hybrid_rerank | 0.400 | 0.800 | 0.800 | 0.800 | 0.656 | 0.688 | 1600 |
| recursive_mpnet | dense | 0.280 | 0.733 | 0.667 | 0.733 | 0.583 | 0.607 | 27 |
| recursive_mpnet | hybrid | 0.373 | 0.800 | 0.800 | 0.800 | 0.600 | 0.641 | 168 |
| recursive_mpnet | rerank | 0.387 | 0.800 | 0.733 | 0.800 | 0.639 | 0.696 | 1568 |
| recursive_mpnet | hybrid_rerank | 0.400 | 0.800 | 0.733 | 0.800 | 0.639 | 0.678 | 1730 |

Top performer here is `markdown_mpnet × hybrid_rerank` however `markdown_bge x hybrid_rerank` was close enough that it was worth benchmarking both of them against each other on RAGAS.


## 3. Generation Evaluation (RAGAS)

RAGAS evaluation was run on the full 30-query master dataset using two retrieval configurations.

### RAG-Only Mode

| Metric | BGE-M3 | MPNET |
|--------|--------|-------|
| Faithfulness | 0.7749 | **0.7903** |
| Answer Relevancy | 0.7199 | **0.7410** |
| Answer Correctness | 0.4814 | **0.4953** |
| Context Precision | 0.6295 | **0.6512** |
| Context Recall | 0.7722 | **0.7816** |

mpnet beat bge on every metric in this test as well making it the clear winner
### Full Mode (MPNET + hybrid_rerank)

| Metric | RAG-Only | Full Mode |
|--------|----------|-----------|
| Faithfulness | 0.7903 | **0.8285** |
| Answer Relevancy | 0.7410 | 0.6922 |
| Answer Correctness | 0.4953 | **0.5125** |
| Context Precision | 0.6512 | **0.6824** |
| Context Recall | 0.7816 | **0.8111** |


Full mode added supervisor query rewrite which led to higher recall and precision but lower relevancy since it strips the query of its style(and we have colliqual queries in the test set which further tanks relevancy score)
added chain of thought to the RAG agent's system prompt as well which led to higher faithfullness because it forces it to reason before answering as well as slightly higher correctness.
correctness score is low here because the LLM is very verbose however tests showed that most of the verbosity is relevant information making this metric not very relevant in this case.

## 4. Agent Routing Accuracy

Evaluated on 8 test cases covering all routing paths.

| Test Case | Expected Route | Actual Route | Correct |
|-----------|---------------|--------------|---------|
| Clear path foul (NBA specified) | rag_agent | rag_agent | Yes |
| Traveling rules (FIBA vs NBA comparison) | rag_agent | rag_agent | Yes |
| Unsportsmanlike foul (no league) | rag_agent + league prompt | rag_agent + league prompt | Yes |
| NBA scoring leader (live stats) | web_agent | web_agent | Yes |
| LeBron points yesterday | web_agent | web_agent | Yes |
| Doncic 14th tech foul | web_agent + mcp_suspension | web_agent + mcp_suspension | Yes |
| Jokic performance score | web_agent + mcp_performance | web_agent + mcp_performance | Yes |
| Grade LeBron's last game | web_agent + mcp_performance | web_agent + mcp_performance | Yes |

**Agent Selection Accuracy: 8/8 (100%)**
**League Detection Accuracy: 8/8 (100%)**



## 5. Failure Cases

### Case 1: 3x3 Offensive Foul in Penalty (Model Reasoning Failure)

**Query:** "FIBA 3x3: A team is in the penalty (7 team fouls). A player on that team commits an offensive foul. Does the other team shoot free throws?"

**System Answer:** "Yes, the other team will shoot free throws. According to the rules, if a team is in the penalty situation (7 team fouls), the non-offending team is awarded free throws for any personal foul, including offensive fouls."

**Correct Answer:** No. Offensive fouls never result in free throws in FIBA 3x3. The penalty (free throws after 7 team fouls) applies only to defensive fouls. An offensive foul results in a turnover regardless of the team foul count.

**Analysis:**
- **Type:** Model reasoning failure
- **Root Cause:** The RAG retrieved the correct source (Art. 34.2.1 on penalty free throws) but the LLM incorrectly generalized it to include offensive fouls. The rule applies specifically to defensive personal fouls, but the model failed to distinguish the edge case.
---

### Case 2: MCP Suspension Tool Off-Season Data (Design Failure)

**Query:** "Is Luka Doncic at risk of suspension this season?"

**System Answer:** Returns a response indicating 0 technical fouls and no suspension risk, presenting these as current facts.

**Correct Answer:** The system should indicate that it cannot determine current suspension risk because the NBA season is not active, or that the data is unavailable.

**Analysis:**
- **Type:** Design failure (external tool integration)
- **Root Cause:** The MCP suspension calculator API does not distinguish between "the player has 0 technical fouls" and "no season data is available." During the off-season, it returns zeroes for all fields rather than a status flag indicating data unavailability.
---

### Case 3: Trent Tucker Rule — Retrieval Miss + Hallucinated Answer (Dual Failure)

**Query:** "NBA: The shot clock is at 0.1 seconds. A player catches an inbounds pass and immediately shoots it before the buzzer. It goes in. Does it count?"

**System Answer:** "The shot counts because the ball left the player's hand before the shot clock expired and made contact with the basket ring."

**Correct Answer:** No. Under the Trent Tucker rule, a player cannot catch and shoot a field goal with less than 0.3 seconds remaining on the game or shot clock. With 0.1 seconds, the ball can only be legally tipped or tapped into the basket.

**Analysis:**
- **Type:** Retrieval failure
- **Root Cause:** The retrieval pipeline (Context Recall = 0.0) failed to surface the NBA's 0.3-second rule (commonly known as the "Trent Tucker rule"), which is a niche timing regulation. Without the relevant rule in its context, the model defaulted to general shot clock logic and confidently produced a wrong answer (Faithfulness = 1.0 to the irrelevant context it received). While the model would usually say it doesnt have enough information to answer, in this case the retrieved context sounded relevant for the model to confidently answer which makes this a silent failure that will make the user assume (since the LLM was confident) that this is how the rule actually works.

