import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

def migrate():
    # 1. Connect to the local SQLite database
    print("Connecting to local SQLite Qdrant database...")
    local_client = QdrantClient(path="./qdrant_data")
    
    # 2. Connect to the running Docker Server
    print("Connecting to Docker Qdrant Server...")
    remote_client = QdrantClient(url="http://localhost:6333")
    
    collections = ["markdown_mpnet", "markdown_bge_m3", "recursive_mpnet", "recursive_bge_m3"]
    
    for coll in collections:
        try:
            print(f"Migrating collection: {coll}...")
            # Fetch all points from local
            points, _ = local_client.scroll(
                collection_name=coll,
                limit=10000,
                with_payload=True,
                with_vectors=True
            )
            
            if not points:
                print(f"No points found in {coll}.")
                continue
                
            print(f"Found {len(points)} points. Recreating on server...")
            
            # Recreate on server with both dense and sparse configurations
            col_info = local_client.get_collection(coll)
            remote_client.recreate_collection(
                collection_name=coll,
                vectors_config=col_info.config.params.vectors,
                sparse_vectors_config=col_info.config.params.sparse_vectors
            )
            
            # Upload points
            remote_client.upload_points(
                collection_name=coll,
                points=points,
                batch_size=100
            )
            print(f"Successfully migrated {coll} to Docker Server!")
            
        except Exception as e:
            print(f"Skipped {coll}: {str(e)}")

if __name__ == "__main__":
    migrate()
