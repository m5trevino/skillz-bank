import sys
import json
import chromadb
from pathlib import Path

# --- CONFIG ---
CHROMA_DB_PATH = "/home/flintx/chat-memory-engine/chroma_db"
COLLECTION_NAME = "ai_chat_logs"

def query_vault(query_text, project_filter=None):
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME)
    
    # Simple semantic query (using the embedding function already defined in collection)
    results = collection.query(
        query_texts=[query_text],
        n_results=5,
        where={"project_context": project_filter} if project_filter else None
    )
    
    # Format output for the Agent
    output = []
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        output.append(f"SOURCE: {meta.get('source_file')} | ENTRY: {meta.get('entry_number')}\nCONTENT: {doc}\n---")
    
    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 query_vault.py <query> [project]")
        sys.exit(1)
        
    query = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(query_vault(query, project))
