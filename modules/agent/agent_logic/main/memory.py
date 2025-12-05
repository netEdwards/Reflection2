
from csv import excel_tab
from datetime import datetime
import logging
from typing import List, Literal, Optional, Sequence, Tuple
from unicodedata import category
from uuid import uuid4
from attr import dataclass
import chromadb
from chromadb.config import Settings
from torch import embedding

from modules.vectors.components.e_model import EmbeddingModel
from modules.vectors.settings import get_settings


@dataclass
class Memory:
    id: str
    text: str
    kind: Literal["episodic", "semantic"]
    category:  str
    tags: list[str]
    importance: float
    created_at: datetime
    source_ids: list[str]
    
class MemoryStore:
    """
    Class to centeralize all main memory/data operations. 
    """
    def __init__(self, collection_name: str = "reflection_memories", embedder: Optional[EmbeddingModel] = None) -> None:
        cfg = get_settings()
        
        self.client = chromadb.PersistentClient(
            path=str(cfg.chroma_dir), #stringified 
            settings = Settings(allow_reset=True), 
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        self.embedder = embedder or EmbeddingModel(
            model_name=cfg.openai_embedding_model,
            batch_size=cfg.openai_embedding_batch_size,
        )
        
    def add(self, memory: Memory) -> Memory:
        mem_id = memory.id or str(uuid4())
        memory.id = mem_id
        embedding = self.embedder.embed([memory.text])[0]
        
        self.collection.add(
            ids=[mem_id],
            documents=[memory.text],
            embeddings=[embedding],
            metadatas=[self._to_metadata(memory)],
        )
        return memory 
    def add_many(self, memories: Sequence[Memory]) -> Memory:
        ids: List[str] = []
        texts: List[str] = []
        metadatas: List[dict] = []
        
        for m in memories:
            mem_id = m.id or str(uuid4())
            m.id = mem_id
            ids.append(mem_id)
            texts.append(m.text)
            metadatas.append(m.metadata)
            
        embeddings = self.embedder.embed(texts=texts)
        
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        
        return list(memories)
    
    def get(self, mem_id: str) -> Optional[Memory]:
        res = self.collection.get(ids=[mem_id])
        if not res["ids"]:
            return None
        return self._from_chroma_row(
            res["ids"][0],
            res["documents"][0],
            res["metadatas"][0],
        )
        
    def search(
        self,
        query: str,
        k: int = 10,
        kind: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Tuple[Memory, float]]:
        """
            Semantic search and filtered search of memory collection.
        """
        where: dict = {}
        if kind:
            where["kind"] = kind
        if category:
            where["category"] = category
        if tags:
            where["tags"] = {"$in": tags}
            
        raw = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where,
        )
        
        ids = raw["ids"][0]
        docs = raw["documents"][0]
        metas = raw["metadatas"][0]
        dists = raw["distances"][0]
        
        scored: List[Tuple[float, Memory]] = []
        now = datetime.now()
        
        for mem_id, text, meta, dist in zip(ids, docs, metas, dists):
            mem = self._from_chroma_row(mem_id, text, meta)
            
            sim = 1.0 - float(dist)
            
            imp = float(meta.get("importance"))
            created_str = meta.get("created_at")
            try:
                created = datetime.fromisoformat(created_str) if created_str else now
            except Exception:
                created = now
                print("Failed to extract creation time, falling to `now`")
                
            age_days = max((now - created).days, 0)
            recency = 1.0 / (1.0 + age_days / 30.0)
            
            score = 0.6 * sim + 0.25 * imp + 0.15 * recency
            scored.append((score, mem))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(m, s) for s, m in scored]
    
    def delete(self, mem_id: str) -> None:
        self.collection.delete(ids=[mem_id])
        
    def delete_all(self) -> None:
        """Only use during dev"""
        self.collection.delete(where={})
        
    @staticmethod
    def _to_metadata(memory: Memory) -> dict:
        return {
            "kind": memory.kind,
            "category": memory.category,
            "tags": memory.tags,
            "importance": float(memory.importance),
            "created_at": memory.created_at.isoformat(),
            "source_ids": memory.source_ids,
        }
        
    @staticmethod
    def _from_chroma_row(mem_id: str, text: str, meta: dict) -> Memory:
        created_raw = meta.get("created_at")
        try:
            created_at = datetime.fromisoformat(created_raw) if created_raw else datetime.utcnow()
        except Exception:
            created_at = datetime.utcnow()

        return Memory(
            id=mem_id,
            text=text,
            kind=meta.get("kind", "semantic"),
            category=meta.get("category", "misc"),
            tags=list(meta.get("tags", [])) or [],
            importance=float(meta.get("importance", 0.5)),
            created_at=created_at,
            source_ids=list(meta.get("source_ids", [])) or [],
        )