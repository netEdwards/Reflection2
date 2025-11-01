# vectors/components/e_model.py

import os
from typing import List, Literal
from langchain_openai import OpenAIEmbeddings


class EmbeddingModel:
    def __init__(self, model_type: Literal["openai"] = "openai"):
        self.model_type = model_type

        if model_type == "openai":
            self._init_openai()
        else:
            raise NotImplementedError(f"Unsupported model type: {model_type}")

    def _init_openai(self):
        api_key = os.getenv("OPENAI_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_KEY not found in environment.")

        self.model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
            show_progress_bar=True  # Optional
        )

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.embed_documents(texts)
