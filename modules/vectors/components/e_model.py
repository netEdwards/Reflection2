# vectors/components/e_model.py

from typing import List
import lmstudio as lms
from modules.vectors.settings import get_settings


class EmbeddingModel:
    def __init__(
        self,
        model_name: str | None = None,
        batch_size: int | None = None,
        max_tokens_per_batch: int | None = None,
    ):
        config = get_settings()
        self.model_name = model_name or config.embedding_model
        self.batch_size = config.embedding_batch_size if batch_size is None else batch_size
        self.max_tokens_per_batch = max_tokens_per_batch

        # lazily loads the model in LM Studio if it isn't already resident
        self.model = lms.embedding_model(self.model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of document chunks for storage.

        Nomic embedding models are trained with asymmetric task prefixes —
        documents and queries must be embedded differently or retrieval quality drops.
        """
        prefixed = [f"search_document: {t}" for t in texts]
        all_vectors: List[List[float]] = []

        batch: list[str] = []
        cur_tokens = 0

        def empty_batch():
            nonlocal batch, cur_tokens, all_vectors
            if not batch:
                return

            batch_vectors = self.model.embed(batch)
            all_vectors.extend(batch_vectors)
            batch = []
            cur_tokens = 0

        for t in prefixed:
            batch.append(t)

            if self.max_tokens_per_batch is not None:
                cur_tokens += max(1, len(t) // 4)

            if len(batch) >= self.batch_size:
                empty_batch()
            elif self.max_tokens_per_batch is not None and cur_tokens >= self.max_tokens_per_batch:
                empty_batch()

        empty_batch()

        return all_vectors

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string for retrieval (see note on prefixes in `embed`)."""
        return self.model.embed(f"search_query: {text}")
