import os
import chromadb
from chromadb.config import Settings
from core.config import settings

class MemoryStore:
    def __init__(self):
        # Initialize local persistent ChromaDB client
        db_path = settings.DB_PATH
        if not os.path.exists(db_path):
            os.makedirs(db_path)
            
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Core memory collections
        self.semantic_memory = self.client.get_or_create_collection(name="semantic_memory")
        self.knowledge_memory = self.client.get_or_create_collection(name="knowledge_memory")

    def store_fact(self, fact: str, metadata: dict = None):
        """Store a semantic fact about the user or system."""
        doc_id = str(hash(fact))
        self.semantic_memory.add(
            documents=[fact],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return doc_id

    def search_facts(self, query: str, n_results: int = 5):
        """Search the semantic memory."""
        results = self.semantic_memory.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

memory_store = MemoryStore()
