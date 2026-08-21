
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
PARSED_DIR = DATA_DIR / "parsed"
IMAGE_CACHE_PATH = DATA_DIR / "image_cache.json"
TEST_DATASET_PATH = DATA_DIR / "test_benchmark_dataset_master.json"
QDRANT_PATH = os.getenv("QDRANT_PATH", str(PROJECT_ROOT / "qdrant_data"))
QDRANT_URL = os.getenv("QDRANT_URL", "")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen-2.5-72b-instruct")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen/qwen2.5-vl-72b-instruct")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda")

ROUTE_MODE = os.getenv("ROUTE_MODE", "full")  
RETRIEVAL_PIPELINE = os.getenv("RETRIEVAL_PIPELINE", "hybrid_rerank") 
RETRIEVAL_COLLECTION = os.getenv("RETRIEVAL_COLLECTION", "markdown_mpnet")
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "basketball_assistant")
SYSTEM_B_URL = os.getenv("SYSTEM_B_URL", "http://localhost:8001")
MCP_SUSPENSION_URL = os.getenv("MCP_SUSPENSION_URL", "http://localhost:5002")
MCP_PERFORMANCE_URL = os.getenv("MCP_PERFORMANCE_URL", "http://localhost:5003")

PDF_LEAGUE_MAP = {
    "documents-corporate-fiba-official-rules-2026-v1-1.pdf": "FIBA",
    "Official-2025-26-NBA-Playing-Rules.pdf": "NBA",
    "2025-26 Men's Basketball Rules Book-BR26.pdf": "NCAA",
    "fiba-3x3-basketball-rules-full-version.pdf": "FIBA_3x3",
}

COLLECTION_CONFIGS = {
    "markdown_bge_m3":   {"chunker": "markdown",   "embedder": "bge_m3",  "dim": 1024},
    "markdown_mpnet":    {"chunker": "markdown",   "embedder": "mpnet",   "dim": 768},
    "recursive_bge_m3":  {"chunker": "recursive",  "embedder": "bge_m3",  "dim": 1024},
    "recursive_mpnet":   {"chunker": "recursive",  "embedder": "mpnet",   "dim": 768},
}

EMBEDDING_MODELS = {
    "bge_m3": "BAAI/bge-m3",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
}

RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "2000"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))

for league in PDF_LEAGUE_MAP.values():
    (IMAGES_DIR / league).mkdir(parents=True, exist_ok=True)
PARSED_DIR.mkdir(parents=True, exist_ok=True)

import logging as _logging

_config_logger = _logging.getLogger("config")


def validate_config():
    errors = []
    warnings = []

    if not OPENROUTER_API_KEY:
        errors.append("OPENROUTER_API_KEY is not set — LLM calls will fail")
    if not GOOGLE_API_KEY:
        warnings.append("GOOGLE_API_KEY is not set — System B web search will fail")
    if not QDRANT_URL and not QDRANT_PATH:
        warnings.append("Neither QDRANT_URL nor QDRANT_PATH is set — vector search may fail")

    for w in warnings:
        _config_logger.warning(f"[CONFIG] {w}")

    if errors:
        for e in errors:
            _config_logger.error(f"[CONFIG] {e}")
        raise ValueError(
            "Missing required configuration. Fix the following:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
