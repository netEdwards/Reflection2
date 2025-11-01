#vectors/components/embedding.py

from modules.vectors.components.e_model import EmbeddingModel

embedding_model = EmbeddingModel(model_type="openai")

def embed_chunks(chunks: list[str]):
    embeddings = embedding_model.embed(chunks)
    return [
        {"text": chunk, "embedding": embedding}
        for chunk, embedding in zip(chunks, embeddings)
    ]
