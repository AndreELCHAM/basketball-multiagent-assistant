"""
Centralized configuration loading from environment variables.
All external model endpoints, API keys, and paths are configured here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Project Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
PARSED_DIR = DATA_DIR / "parsed"
IMAGE_CACHE_PATH = DATA_DIR / "image_cache.json"
TEST_DATASET_PATH = DATA_DIR / "test_benchmark_dataset.json"
QDRANT_PATH = os.getenv("QDRANT_PATH", str(PROJECT_ROOT / "qdrant_data"))
QDRANT_URL = os.getenv("QDRANT_URL", "")  # e.g. "http://qdrant:6333" in Docker

# ── API Keys ───────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── Model Config ───────────────────────────────────────────────────────────
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen-2.5-72b-instruct")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen/qwen2.5-vl-72b-instruct")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda")

# ── Routing ────────────────────────────────────────────────────────────────
ROUTE_MODE = os.getenv("ROUTE_MODE", "rag_only")  # "rag_only" | "full"

# ── Retrieval ──────────────────────────────────────────────────────────────
RETRIEVAL_PIPELINE = os.getenv("RETRIEVAL_PIPELINE", "dense")  # "dense" | "hybrid" | "rerank"
RETRIEVAL_COLLECTION = os.getenv("RETRIEVAL_COLLECTION", "markdown_mpnet")
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# ── Service URLs (Docker inter-container communication) ────────────────
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
SYSTEM_B_URL = os.getenv("SYSTEM_B_URL", "http://localhost:8001")
MCP_RULES_URL = os.getenv("MCP_RULES_URL", "http://localhost:5001")
MCP_FOUL_URL = os.getenv("MCP_FOUL_URL", "http://localhost:5002")

# ── PDF-to-League Mapping ─────────────────────────────────────────────────
PDF_LEAGUE_MAP = {
    "documents-corporate-fiba-official-rules-2026-v1-1.pdf": "FIBA",
    "Official-2025-26-NBA-Playing-Rules.pdf": "NBA",
    "2025-26 Men's Basketball Rules Book-BR26.pdf": "NCAA",
    "fiba-3x3-basketball-rules-full-version.pdf": "FIBA_3x3",
}

# ── Qdrant Collection Names ───────────────────────────────────────────────
COLLECTION_CONFIGS = {
    "markdown_bge_m3":   {"chunker": "markdown",   "embedder": "bge_m3",  "dim": 1024},
    "markdown_mpnet":    {"chunker": "markdown",   "embedder": "mpnet",   "dim": 768},
    "recursive_bge_m3":  {"chunker": "recursive",  "embedder": "bge_m3",  "dim": 1024},
    "recursive_mpnet":   {"chunker": "recursive",  "embedder": "mpnet",   "dim": 768},
}

# ── Embedding Model IDs ───────────────────────────────────────────────────
EMBEDDING_MODELS = {
    "bge_m3": "BAAI/bge-m3",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
}

RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

# ── Ensure directories exist ──────────────────────────────────────────────
for league in PDF_LEAGUE_MAP.values():
    (IMAGES_DIR / league).mkdir(parents=True, exist_ok=True)
PARSED_DIR.mkdir(parents=True, exist_ok=True)
