
import asyncio
import concurrent.futures
import json
import logging
import re
import sys
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, field_validator
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.graph import run_query
from src.agents.guardrails import check_input, check_output
from src.config import (
    SYSTEM_B_URL,
    MCP_SUSPENSION_URL,
    MCP_PERFORMANCE_URL,
    MONGODB_URL,
    MONGODB_DB_NAME,
    DATA_DIR,
    IMAGES_DIR,
    MAX_QUERY_LENGTH,
    RATE_LIMIT_PER_MINUTE,
    MAX_CONVERSATION_HISTORY,
    validate_config,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def sanitize_input(text: str) -> str:
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)


class RateLimiter:

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            return False

        self._requests[client_ip].append(now)
        return True

    def cleanup(self):
        now = time.time()
        window_start = now - self.window_seconds
        stale_ips = [
            ip for ip, times in self._requests.items()
            if not times or times[-1] < window_start
        ]
        for ip in stale_ips:
            del self._requests[ip]


rate_limiter = RateLimiter(max_requests=RATE_LIMIT_PER_MINUTE, window_seconds=60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("System A starting up — validating configuration...")
    try:
        validate_config()
        logger.info("Configuration validation passed")
    except ValueError as e:
        logger.error(f"Configuration validation FAILED: {e}")

    yield

    logger.info("System A shutting down...")
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")


app = FastAPI(
    title="System A — Basketball Multi-Agent Assistant",
    description="LangGraph-powered multi-agent pipeline for basketball rules, analytics & live data",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# MongoDB

mongo_client = None
db = None


def get_db():
    global mongo_client, db
    if db is None:
        mongo_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        db = mongo_client[MONGODB_DB_NAME]
        db.threads.create_index("thread_id", unique=True)
        db.threads.create_index("updated_at")
        logger.info(f"Connected to MongoDB: {MONGODB_URL}/{MONGODB_DB_NAME}")
    return db


# Request and response models

class ChatRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None
    league: Optional[str] = None

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be empty')
        if len(v) > MAX_QUERY_LENGTH:
            raise ValueError(f'Query too long ({len(v)} chars). Maximum is {MAX_QUERY_LENGTH} characters.')
        return sanitize_input(v)


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    response_type: str
    language: str
    league_filter: Optional[str]
    chunks: list[dict]
    image_paths: list[str]
    mcp_results: Optional[dict] = None
    web_results: Optional[dict] = None
    human_input_options: Optional[list[str]] = None
    human_input_message: Optional[str] = None


class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class ThreadDetail(BaseModel):
    thread_id: str
    title: str
    messages: list[dict]
    created_at: str
    updated_at: str


class QueryRequest(BaseModel):
    query: str
    league: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    language: str
    league_filter: Optional[str]
    chunks: list[dict]
    image_paths: list[str]


# Helpers

def _generate_title(query: str) -> str:
    title = query.strip()[:80]
    if len(query) > 80:
        title += "..."
    return title


def _get_thread(thread_id: str) -> Optional[dict]:
    try:
        database = get_db()
        return database.threads.find_one({"thread_id": thread_id}, {"_id": 0})
    except Exception as e:
        logger.warning(f"MongoDB unavailable, thread lookup skipped: {e}")
        return None


def _save_thread(thread_id: str, title: str, messages: list[dict]):
    try:
        database = get_db()
        now = datetime.now(timezone.utc).isoformat()
        database.threads.update_one(
            {"thread_id": thread_id},
            {
                "$set": {
                    "thread_id": thread_id,
                    "title": title,
                    "messages": messages,
                    "updated_at": now,
                    "message_count": len(messages),
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )
    except Exception as e:
        logger.warning(f"MongoDB unavailable, thread save skipped: {e}")


# Endpoints

@app.get("/api/health")
def health_check():
    mongo_ok = False
    try:
        database = get_db()
        database.command("ping")
        mongo_ok = True
    except Exception:
        pass

    return {
        "status": "ok",
        "system": "A",
        "framework": "LangGraph",
        "mongodb": "connected" if mongo_ok else "unavailable",
        "services": {
            "system_b": SYSTEM_B_URL,
            "mcp_suspension": MCP_SUSPENSION_URL,
            "mcp_performance": MCP_PERFORMANCE_URL,
        },
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, req: Request):
    # Rate limiting
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_PER_MINUTE} requests per minute.",
        )

    # Get or create thread
    thread_id = request.thread_id or str(uuid.uuid4())
    thread = _get_thread(thread_id)

    conversation_history = []
    title = ""

    if thread:
        conversation_history = thread.get("messages", [])
        title = thread.get("title", "")
    else:
        title = _generate_title(request.query)

    logger.info(
        f"Chat: thread={thread_id[:8]}..., query='{request.query[:80]}...', "
        f"history={len(conversation_history)} msgs"
    )

    # Handle league selection response from human in the loop
    league_override = request.league
    if (conversation_history
        and conversation_history[-1].get("response_type") == "league_prompt"):

        text = request.query.upper()
        if not league_override:
            if "NBA" in text:
                league_override = "NBA"
            elif "NCAA" in text or "COLLEGE" in text:
                league_override = "NCAA"
            elif "3X3" in text:
                league_override = "FIBA_3x3"
            elif "FIBA" in text:
                league_override = "FIBA"

        # Recover original query before the league prompt
        original_query = ""
        for msg in reversed(conversation_history):
            if msg.get("role") == "user" and msg.get("response_type") != "league_prompt":
                original_query = msg.get("content", "")
                break

        if original_query:
            logger.info(f"  Recovered original query: '{original_query}' with league '{league_override}'")
            request.query = original_query

    # Cap history to avoid LLM context overflow
    recent_history = conversation_history[-MAX_CONVERSATION_HISTORY:] if conversation_history else []
    if len(conversation_history) > MAX_CONVERSATION_HISTORY:
        logger.info(
            f"  Capped conversation history: {len(conversation_history)} -> {MAX_CONVERSATION_HISTORY} messages"
        )

    # Input guardrail
    input_check = check_input(request.query)
    if not input_check.passed:
        logger.info(f"  Input guard BLOCKED: {input_check.reason}")
        return ChatResponse(
            thread_id=thread_id,
            answer=input_check.blocked_message,
            response_type="guardrail_block",
            language="en",
            league_filter=None,
            chunks=[],
            image_paths=[],
        )

    # Run the langgraph pipeline with timeout
    REQUEST_TIMEOUT = 180
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                run_query,
                query=request.query,
                league=league_override,
                thread_id=thread_id,
                conversation_history=recent_history,
            )
            state = future.result(timeout=REQUEST_TIMEOUT)
    except concurrent.futures.TimeoutError:
        logger.error(f"Pipeline timed out after {REQUEST_TIMEOUT}s")
        return ChatResponse(
            thread_id=thread_id,
            answer=f"Request timed out after {REQUEST_TIMEOUT} seconds. The model may be overloaded. Please try again.",
            response_type="error",
            language="en",
            league_filter=None,
            chunks=[],
            image_paths=[],
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return ChatResponse(
            thread_id=thread_id,
            answer="An internal error occurred while processing your query. Please try again.",
            response_type="error",
            language="en",
            league_filter=None,
            chunks=[],
            image_paths=[],
        )

    response_type = state.get("response_type", "answer")
    answer = state.get("final_answer", "No answer generated.")

    # Output guardrail
    output_check = check_output(request.query, answer)
    if not output_check.passed:
        logger.info(f"  Output guard BLOCKED: {output_check.reason}")
        answer = output_check.blocked_message
        response_type = "guardrail_block"

    chunks = [
        {
            "text": c.get("text", ""),
            "metadata": c.get("metadata", {}),
            "score": c.get("score", 0.0),
        }
        for c in state.get("retrieved_chunks", [])
    ]

    # Save user and assistant messages to thread history
    conversation_history.append({
        "role": "user",
        "content": request.query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    conversation_history.append({
        "role": "assistant",
        "content": answer,
        "response_type": response_type,
        "league_filter": state.get("league_filter"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    _save_thread(thread_id, title, conversation_history)

    return ChatResponse(
        thread_id=thread_id,
        answer=answer,
        response_type=response_type,
        language=state.get("user_language", "en"),
        league_filter=state.get("league_filter"),
        chunks=chunks,
        image_paths=state.get("image_paths", []),
        mcp_results=state.get("mcp_results") or None,
        web_results=state.get("web_search_results") or None,
        human_input_options=state.get("human_input_options") or None,
        human_input_message=state.get("human_input_message") or None,
    )


@app.get("/api/threads")
def list_threads():
    try:
        database = get_db()
        threads = list(
            database.threads.find(
                {},
                {"_id": 0, "thread_id": 1, "title": 1, "created_at": 1,
                 "updated_at": 1, "message_count": 1},
            ).sort("updated_at", -1)
        )
        return {"threads": threads}
    except Exception as e:
        logger.warning(f"MongoDB unavailable: {e}")
        return {"threads": []}


@app.get("/api/threads/{thread_id}")
def get_thread(thread_id: str):
    thread = _get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@app.delete("/api/threads/{thread_id}")
def delete_thread(thread_id: str):
    try:
        database = get_db()
        result = database.threads.delete_one({"thread_id": thread_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Thread not found")
        return {"status": "deleted", "thread_id": thread_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"MongoDB unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/api/images/{league}/{filename}")
def serve_image(league: str, filename: str):
    image_path = IMAGES_DIR / league / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(image_path))


# Legacy endpoint not used by frontend
@app.post("/api/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    logger.info(f"[DEPRECATED] API query: '{request.query[:80]}...' league={request.league}")

    state = run_query(request.query, league=request.league)

    chunks = [
        {
            "text": c.get("text", ""),
            "metadata": c.get("metadata", {}),
            "score": c.get("score", 0.0),
        }
        for c in state.get("retrieved_chunks", [])
    ]

    return QueryResponse(
        answer=state.get("final_answer", "No answer generated."),
        language=state.get("user_language", "en"),
        league_filter=state.get("league_filter"),
        chunks=chunks,
        image_paths=state.get("image_paths", []),
    )


# SSE streaming endpoint not used by frontend
@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, req: Request):
    client_ip = req.client.host if req.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_PER_MINUTE} requests per minute.",
        )

    async def event_generator():
        try:
            yield _sse_event("status", {"message": "Processing query..."})

            yield _sse_event("status", {"message": "Checking input guardrails..."})
            input_check = check_input(request.query)
            if not input_check.passed:
                yield _sse_event("result", {
                    "thread_id": request.thread_id or str(uuid.uuid4()),
                    "answer": input_check.blocked_message,
                    "response_type": "guardrail_block",
                })
                yield _sse_event("done", {})
                return

            thread_id = request.thread_id or str(uuid.uuid4())
            thread = _get_thread(thread_id)
            conversation_history = thread.get("messages", []) if thread else []
            title = thread.get("title", "") if thread else _generate_title(request.query)

            recent_history = conversation_history[-MAX_CONVERSATION_HISTORY:] if conversation_history else []

            yield _sse_event("status", {"message": "Routing query to agents..."})

            loop = asyncio.get_event_loop()
            REQUEST_TIMEOUT = 180
            try:
                state = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: run_query(
                            query=request.query,
                            league=request.league,
                            thread_id=thread_id,
                            conversation_history=recent_history,
                        )
                    ),
                    timeout=REQUEST_TIMEOUT,
                )
            except asyncio.TimeoutError:
                yield _sse_event("error", {"message": f"Request timed out after {REQUEST_TIMEOUT}s"})
                yield _sse_event("done", {})
                return
            except Exception as e:
                logger.error(f"Pipeline error: {e}", exc_info=True)
                yield _sse_event("error", {"message": "An internal error occurred. Please try again."})
                yield _sse_event("done", {})
                return

            yield _sse_event("status", {"message": "Checking output safety..."})
            answer = state.get("final_answer", "No answer generated.")
            response_type = state.get("response_type", "answer")

            output_check = check_output(request.query, answer)
            if not output_check.passed:
                answer = output_check.blocked_message
                response_type = "guardrail_block"

            chunks = [
                {"text": c.get("text", ""), "metadata": c.get("metadata", {}), "score": c.get("score", 0.0)}
                for c in state.get("retrieved_chunks", [])
            ]

            conversation_history.append({
                "role": "user",
                "content": request.query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            conversation_history.append({
                "role": "assistant",
                "content": answer,
                "response_type": response_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            _save_thread(thread_id, title, conversation_history)

            yield _sse_event("result", {
                "thread_id": thread_id,
                "answer": answer,
                "response_type": response_type,
                "language": state.get("user_language", "en"),
                "league_filter": state.get("league_filter"),
                "chunks": chunks,
                "image_paths": state.get("image_paths", []),
                "mcp_results": state.get("mcp_results") or None,
                "web_results": state.get("web_search_results") or None,
            })

            yield _sse_event("done", {})

        except Exception as e:
            logger.error(f"SSE stream error: {e}", exc_info=True)
            yield _sse_event("error", {"message": "Stream failed unexpectedly."})
            yield _sse_event("done", {})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
