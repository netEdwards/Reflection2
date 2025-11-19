# vectors/components/e_model.py

import os
from typing import List, Literal
from langchain_openai import OpenAIEmbeddings
import httpx
import certifi
from modules.vectors.settings import get_settings


class EmbeddingModel:
    def __init__(
        self,
        model_type: Literal["openai"] = "openai",
        model_name: str = "text-embedding-3-small",
        batch_size: int | None = None,
        max_tokens_per_batch: int | None = None,
    ):
        config = get_settings()
        self.model_type = model_type
        self.batch_size = config.openai_embedding_batch_size if batch_size is None else batch_size
        self.max_tokens_per_batch = max_tokens_per_batch
        self.model_name = model_name

        if model_type == "openai":
            self._init_openai()
        else:
            raise NotImplementedError(f"Unsupported model type: {model_type}")

    def _init_openai(self):
        api_key = os.getenv("OPENAI_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_KEY not found in environment.")
        
        http_client = httpx.Client(
            verify=certifi.where(),   # same thing that worked in your test
            timeout=30.0,
        )

        self.model = OpenAIEmbeddings(
            model=self.model_name,
            api_key=api_key,
            http_client=http_client,
        )

    def embed(self, texts: List[str]) -> List[List[float]]:
        all_vectors: List[List[float]] = []
        
        batch: list[str] = []
        cur_tokens = 0
        
        def empty_batch():
            nonlocal batch, cur_tokens, all_vectors
            if not batch:
                return
            
            batch_vectors = self.model.embed_documents(batch)
            all_vectors.extend(batch_vectors)
            batch = []
            cur_tokens = 0
            
        for t in texts:
            batch.append(t)
            
            if self.max_tokens_per_batch is not None:
                cur_tokens += max(1, len(t) // 4)
                
            if len(batch) >= self.batch_size:
                empty_batch()
            elif self.max_tokens_per_batch is not None and cur_tokens >= self.max_tokens_per_batch:
                empty_batch()
                
        empty_batch()
        
        return all_vectors
            
"""
Add a fucntion to try to embed with a retry mode. 
"""
