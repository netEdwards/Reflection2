from pathlib import Path
from pyexpat import model
import re
from turtle import heading
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from httpx import head
from modules.vectors import settings
from modules.vectors.settings import get_settings

from modules.vectors.components.e_model import EmbeddingModel

class ChromaVectorStore:
    def __init__(
        self,
    ):
        
        config = get_settings()
        self.persist_directory = config.chroma_dir
        self.collection_name = config.default_collection_name
        
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                allow_reset=True
            )
        )
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        
        if not chunks:
            print("No chunks provided to upsert.")
            return
        
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for c in chunks:
            if "embeddings" not in c:
                print("Embeddings are not present in chunk; skipping.")
                continue
            
            ids.append(c['chunk_id'])
            documents.append(c['text'])
            embeddings.append(c['embeddings'])
            
            raw_hp = c.get("heading_path", [])
            heading_path = _flatten_heading_path(raw_hp)
            
            meta = {
                "document_name": c.get("document_name", ""),
                "document_path": c.get("document_path", ""),
                "heading_path": heading_path,
                "tokens": c.get("tokens")
            }
            
            m = c.get("metadata", {}) or {}
            meta["chunk_index"] = m.get("chunk_index")
            meta["tags"] = m.get("tags", "")
            meta["links"] = m.get("links", "")
            meta = {k: _clean_meta_value(v) for k, v in meta.items()} #sanatize the meta (fixes Path and other issues)
            print("METAS: \n\n")
            print(meta)
            metadatas.append(meta)
            
        if not ids:
            print("No valid chunks to upsert after processing; exiting. (Missing ID's)")
            return
        
        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        except Exception as e:
            print(f"Error during upsert: {e}")
    
    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        embedder: EmbeddingModel = None,
    ):
        if not embedder:
            embedder = EmbeddingModel(
                model_type="openai",
                model_name="text-embedding-3-small",
                batch_size=32,
            )
        try:
            query_vecs = embedder.embed(texts=query_texts)
            if query_vecs is None or len(query_vecs) == 0:
                print("Failed to generate embeddings for query texts.")
                return None
            
            return self.collection.query(
                query_embeddings=query_vecs,
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            print(f"Error during query: {e}")
            return None
        
        
        
def _clean_meta_value(v):
    if isinstance(v, Path):
        return str(v)
    if isinstance(v, list):
        if not v:
            return None #if empty
        return ", ".join(str(_clean_meta_value(i)) for i in v)
    # allowed types for Chroma: str, int, float, bool, None
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)  # last resort

def _flatten_heading_path(heading_path: Any) -> str | None:
    if heading_path is None:
        return None
    if isinstance(heading_path, list):
        # "Top > Section > Subsection"
        return " > ".join(str(h) for h in heading_path)
    return str(heading_path)