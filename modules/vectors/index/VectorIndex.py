from __future__ import annotations

from chromadb import PersistentClient
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from pathlib import Path
from typing import List, Dict, Optional, Callable, Sequence, Any
import hashlib

# Optional: pull in your custom OpenAI embedder if available
try:
    # adjust import path if your package layout differs
    from e_model import EmbeddingModel  # vectors/components/e_model.py in your repo
except Exception:
    EmbeddingModel = None  # soft dependency

EmbeddingFn = Callable[[Sequence[str]], List[List[float]]]


class _AdapterOpenAIEmbeddingFn:
    """Adapts your EmbeddingModel(embed) to Chroma's embedding_function(signature)."""
    def __init__(self, model: "EmbeddingModel"):
        self.model = model
    def __call__(self, texts: Sequence[str]) -> List[List[float]]:
        # Chroma passes List[str]; must return List[List[float]]
        return self.model.embed(list(texts))


class VectorIndex:
    def __init__(
        self,
        persist_path: str = "./.chroma",                 # safer default than "C:\Reflection"
        collection_name: str = "markdown_notes",
        embedding_fn: Optional[EmbeddingFn] = None,      # power users can pass any callable(List[str])->List[List[float]]
        embedding_model: Optional["EmbeddingModel"] = None,  # your OpenAI model wrapper (e_model.py)
    ):
        """
        If embedding_model is provided, it takes precedence.
        Else if embedding_fn is provided, use that.
        Else fall back to Chroma's DefaultEmbeddingFunction (MiniLM).
        """
        self.client = PersistentClient(path=persist_path)

        if embedding_model is not None:
            if EmbeddingModel is None:
                raise ImportError("EmbeddingModel not importable; check e_model.py import.")
            self.embedding_fn: EmbeddingFn = _AdapterOpenAIEmbeddingFn(embedding_model)
        elif embedding_fn is not None:
            self.embedding_fn = embedding_fn
        else:
            self.embedding_fn = DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def _hash_file(self, path: str) -> str:
        with open(path, 'rb') as f:
            data = f.read()
        return hashlib.md5(data).hexdigest()

    def add_documents(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def delete_documents_by_path(self, doc_path: str):
        # Delete all chunks that reference this document path
        results = self.collection.get(where={"path": doc_path})
        ids_to_delete = results.get("ids", [])
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

    def get_all_paths(self) -> List[str]:
        # Retrieve all unique document paths
        results = self.collection.get()
        return list({meta["path"] for meta in results.get("metadatas", []) if "path" in meta})

    def query(self, query_text: str, k: int = 5) -> List[Dict]:
        results = self.collection.query(query_texts=[query_text], n_results=k)
        return [
            {
                "id": rid if i < len(results.get("ids", [[]])[0]) else None,
                "text": doc,
                "metadata": meta,
                "score": score  # NOTE: distance; lower is better
            }
            for i, (doc, meta, score, rid) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
                results.get("ids", [[]])[0],
            ))
        ]

    def rebuild(self):
        # Recreate the collection with the currently bound embedding function
        name = self.collection.name
        self.client.delete_collection(name=name)
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn
        )
