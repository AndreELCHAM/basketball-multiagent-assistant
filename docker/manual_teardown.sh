#!/bin/bash
# ============================================================
# Method 1: Manual Docker Teardown
# ============================================================

echo "Stopping containers..."
docker stop frontend system-a system-b mcp-foul-calculator mcp-rules-lookup mongodb qdrant

echo "Removing containers..."
docker rm frontend system-a system-b mcp-foul-calculator mcp-rules-lookup mongodb qdrant

echo "Removing networks..."
docker network rm frontend-net rag-net backend-net

echo "Done. (Volumes qdrant_storage and mongo_data were NOT removed. Use 'docker volume rm' to delete them if needed.)"
