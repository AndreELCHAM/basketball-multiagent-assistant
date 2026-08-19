


docker network create frontend-net   
docker network create rag-net          
docker network create backend-net     

docker run -d --name qdrant --network rag-net \
  -p 6333:6333 -v "$(pwd)/qdrant_data:/qdrant/storage" \
  qdrant/qdrant:latest

docker run -d --name mongodb --network backend-net \
  -p 27017:27017 -v mongo_data:/data/db \
  mongo:7


docker build -t mcp-rules-lookup ./mcp_servers/rules_lookup
docker run -d --name mcp-rules-lookup --network backend-net \
  -p 5001:5001 mcp-rules-lookup

docker build -t mcp-foul-calculator ./mcp_servers/foul_calculator
docker run -d --name mcp-foul-calculator --network backend-net \
  -p 5002:5002 mcp-foul-calculator


docker build -t system-b ./system_b
docker run -d --name system-b --network backend-net \
  -e MONGODB_URL=mongodb://mongodb:27017 \
  -e MCP_RULES_URL=http://mcp-rules-lookup:5001 \
  -e MCP_FOUL_URL=http://mcp-foul-calculator:5002 \
  -p 8001:8001 system-b


docker build -t system-a .
docker run -d --name system-a --network frontend-net \
  --env-file .env \
  -e QDRANT_URL=http://qdrant:6333 \
  -e MONGODB_URL=mongodb://mongodb:27017 \
  -e SYSTEM_B_URL=http://system-b:8001 \
  -e MCP_RULES_URL=http://mcp-rules-lookup:5001 \
  -e MCP_FOUL_URL=http://mcp-foul-calculator:5002 \
  -e EMBEDDING_DEVICE=cpu \
  -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  system-a


docker network connect rag-net system-a
docker network connect backend-net system-a


docker build -t frontend ./frontend
docker run -d --name frontend --network frontend-net \
  -p 3000:80 frontend

# 8. Verify
echo "=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Network Membership ==="
docker network inspect frontend-net --format '{{range .Containers}}{{.Name}} {{end}}'
docker network inspect rag-net --format '{{range .Containers}}{{.Name}} {{end}}'
docker network inspect backend-net --format '{{range .Containers}}{{.Name}} {{end}}'
echo ""
curl http://localhost:8000/api/health
curl http://localhost:8001/health
