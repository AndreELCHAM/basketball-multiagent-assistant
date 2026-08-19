# 📋 Development Changelog

> Documenting every change made to the Basketball Multiagent Assistant for presentation purposes.

---

## 2026-08-18 — Image Extraction Filtering Pipeline

### 🔴 Problem

Running `python scripts/run_ingestion.py` extracted **2,989 images** (41 MB) from 4 basketball rulebook PDFs (FIBA, NBA, NCAA, FIBA 3x3). The vast majority were **junk** — tiny logos, separator bars, decorative headers, watermarks, page backgrounds — not actual basketball diagrams.

Sending all of these to the VLM captioner (Qwen2.5-VL-72B via OpenRouter) would have:
- **Wasted API credits** on captioning logos and separators
- **Polluted the RAG knowledge base** with nonsense captions
- **Caused hallucinations** — the VLM would try to describe a random logo as a "basketball court diagram"

### 🟡 Investigation

Analyzed the size distribution of all 2,989 extracted images:

| Size Bucket | Count | Typical Content |
|---|---|---|
| Under 5 KB | 1,149 | Tiny icons, dots, 1px spacers |
| 5–20 KB | 1,348 | Small logos, repeated headers, **NBA referee signals** |
| 20–50 KB | 347 | Mixed — some useful, some decorative |
| Over 50 KB | 145 | Court diagrams, large illustrations |

Key finding: the **NBA rulebook** stores referee signal illustrations as small individual images (5–20 KB, 100–300px), while **FIBA** uses larger composite images. A naive file-size-only filter would kill legitimate NBA content.

### 🟢 Solution — Smart 3-Layer Image Filter

Added filtering in [`src/ingestion/pdf_parser.py`](src/ingestion/pdf_parser.py) with three checks:

```python
MIN_IMAGE_FILE_SIZE = 5 * 1024    # 5 KB   — skip truly tiny icons / dots
MIN_IMAGE_DIMENSION = 100         # pixels — both width AND height must exceed
MAX_ASPECT_RATIO = 3.5            # reject thin separator bars / banners
```

| Filter | What it catches | Example |
|---|---|---|
| **File size ≥ 5 KB** | Micro-icons, 1px spacers, bullet dots | 2 KB logo fragment |
| **Dimensions ≥ 100×100 px** | Small logos, bullet-style icons | 60×60 chapter icon |
| **Aspect ratio ≤ 3.5:1** | Thin horizontal/vertical separator bars | 384×60 banner strip, 231×51 line |

This reduced the image count from **~2,989 → ~120–150 meaningful diagrams** while preserving all legitimate content (court layouts, referee signals, equipment specs).

### 📁 Files Changed

#### `src/ingestion/pdf_parser.py`
- Added `_is_meaningful_image()` — checks file size, pixel dimensions, and aspect ratio
- Added `_strip_image_refs()` — removes markdown `![](...)` references to discarded images so downstream processing never sees them
- Added `clean_output()` — wipes `data/images/`, `data/parsed/`, and `image_cache.json` before each run for a clean slate
- Modified `parse_pdf()` — filters images after extraction, deletes junk files from disk, logs kept vs. discarded counts
- Added `Pillow` dependency for image dimension checking

#### `scripts/run_ingestion.py`
- Added **Step 0: Clean previous outputs** — calls `clean_output()` at pipeline start so every run is a fresh parse (no stale data from previous runs)

### 📊 Before vs After

| Metric | Before | After |
|---|---|---|
| Total images extracted | 2,989 | ~120–150 |
| Disk usage | 41 MB | ~8–10 MB |
| VLM API calls needed | 2,989 | ~120–150 |
| Junk captions in RAG | Many | Near zero |
| NBA referee signals | ❌ Lost (with aggressive filter) | ✅ Preserved |
| Separator bars / banners | ✅ Kept as junk | ❌ Filtered out |

---

## 2026-08-18 — Qdrant Version Compatibility Fix

### 🔴 Problem

When running `python scripts/benchmark_ingestion.py --fresh` to build the vector databases, the script crashed with the following error:
`AttributeError: 'CollectionInfo' object has no attribute 'vectors_count'`

### 🟡 Investigation

The `vectors_count` attribute was deprecated and completely removed from the `CollectionInfo` object in newer versions of the `qdrant-client` library (v1.7.0+). The benchmark script was trying to read this attribute in `get_collection_info()` just to print collection stats, which caused the crash. 

Since the benchmark results table actually relies on `points_count` to display the "Points in DB" metric, the `vectors_count` variable was entirely unused.

### 🟢 Solution

Removed the `vectors_count` extraction from `src/vectorstore/qdrant_store.py` to ensure compatibility with modern Qdrant client versions.

### 📁 Files Changed

#### `src/vectorstore/qdrant_store.py`
- Modified `get_collection_info()` to remove `info.vectors_count` from the returned dictionary.

---
================================================================================
RETRIEVAL BENCHMARK RESULTS
================================================================================
| Collection       | Pipeline   |   Hit@3 |   Hit@5 |   MRR |   Avg Latency (ms) |
|------------------|------------|---------|---------|-------|--------------------|
| markdown_bge_m3  | dense      |   0.833 |   0.833 | 0.769 |             1061.2 |
| markdown_bge_m3  | hybrid     |   0.778 |   0.833 | 0.792 |              161.7 |
| markdown_bge_m3  | rerank     |   0.889 |   0.889 | 0.889 |            21522   |
| markdown_mpnet   | dense      |   0.889 |   0.944 | 0.835 |              397.7 |
| markdown_mpnet   | hybrid     |   0.889 |   0.889 | 0.833 |              131.8 |
| markdown_mpnet   | rerank     |   0.889 |   0.889 | 0.889 |             1088.4 |
| recursive_bge_m3 | dense      |   0.778 |   0.889 | 0.75  |               55.2 |
| recursive_bge_m3 | hybrid     |   0.833 |   0.833 | 0.833 |              102.7 |
| recursive_bge_m3 | rerank     |   0.889 |   0.889 | 0.889 |             1322.8 |
| recursive_mpnet  | dense      |   0.889 |   0.889 | 0.889 |               29.6 |
| recursive_mpnet  | hybrid     |   0.889 |   0.889 | 0.889 |              178.6 |
| recursive_mpnet  | rerank     |   0.889 |   0.889 | 0.889 |             1640   |

================================================================================
END-TO-END LLM EVALUATION RESULTS (markdown_mpnet × dense)
================================================================================
# LLM End-to-End Evaluation

**Overall Average Score:** 63.1%
**Total Keywords Hit:** 67.4% (62/92)
**Retrieval Hit Rate:** 88.9% (16/18)

|   ID | League   | Query                                            | Chunk Hit   | Score   | Answer Snippet                                                  |
|------|----------|--------------------------------------------------|-------------|---------|-----------------------------------------------------------------|
|    1 | FIBA     | In FIBA, what is the cylinder principle in ba... | ✅           | 100%    | ### Cylinder Principle in FIBA Basketball  The cylinder prin... |
|    2 | NBA      | How many timeouts are allowed per team in an ... | ✅           | 60%     | According to the NBA rulebook, each team is entitled to a sp... |
|    3 | FIBA     | Explain the dimensions and markings of a FIBA... | ✅           | 83%     | ### FIBA Basketball Court Dimensions and Markings  #### **Co... |
|    4 | FIBA     | What are the exact measurements of the basket... | ❌           | 50%     | The provided rulebook sources do not contain specific inform... |
|    5 | FIBA     | In FIBA free throw situations, where exactly ... | ✅           | 100%    | In FIBA free throw situations, the rebounding players must s... |
|    6 | FIBA     | In FIBA, what hand signals do basketball refe... | ERROR       | ERROR   | RetryError[<Future at 0x1f8135decf0 state=finished raised Ba    |
|    7 | FIBA     | Quelles sont les règles du marcher en basketb... | ✅           | 33%     | Les règles de déplacement (traveling) en basketball selon la... |
|    8 | NBA      | Combien de fautes personnelles un joueur peut... | ✅           | 20%     | Dans un match de la NBA, un joueur est disqualifié du jeu lo... |
|    9 | FIBA     | ¿Cuánto tiempo tiene un equipo para avanzar e... | ✅           | 40%     | Según las reglas de la FIBA, un equipo tiene 8 segundos para... |
|   10 |          | ¿Cuáles son las diferencias en la duración de... | ✅           | 0%      | Las diferencias en la duración de los períodos entre la NBA ... |
|   11 | FIBA_3x3 | yo so like what happens when someone gets a t... | ✅           | 60%     | In 3x3 basketball, when a player receives a technical foul, ... |
|   12 | NCAA     | In NCAA, wait can u explain the shot clock th... | ✅           | 100%    | Certainly! Here's a detailed explanation of the shot clock r... |
|   13 | NBA      | bruh what even counts as goaltending in the N... | ✅           | 67%     | To address your question about goaltending in the NBA, we ne... |
|   14 | FIBA_3x3 | how does the 12 second rule work in 3x3 hoops... | ✅           | 80%     | The 12-second rule in 3x3 basketball is designed to ensure t... |
|   15 | NBA      | ok so like in the nba can u challenge a foul ... | ✅           | 100%    | In the NBA, a head coach can challenge a foul call, but ther... |
|   16 | FIBA     | In FIBA, what constitutes a double dribble vi... | ✅           | 100%    | In FIBA, a double dribble violation is not explicitly define... |
|   17 | FIBA     | Define the backcourt violation rules under FI... | ✅           | 83%     | The backcourt violation rules under FIBA regulations are not... |
|   18 | FIBA_3x3 | How many players are on the court in a 3x3 ga... | ✅           | 60%     | In a 3x3 basketball game, each team has 3 players on the cou... |

<!-- Future changes will be appended below this line -->
