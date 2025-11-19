from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from modules.vectors.settings import get_settings
from modules.vectors.index.chroma_store import ChromaVectorStore
from modules.vectors.main_pipeline import pipeline, InvalidMarkdownFileError

@dataclass
class IngestSummary:
    files_processed: int
    total_chunks: int
    errors: List[str]

@dataclass
class QueryResultChunk:
    document: str
    text: str
    score: float
    metadata: Dict[str, Any]

@dataclass
class QueryResult:
    query: str
    results: List[QueryResultChunk]


class VectorService:

    def __init__(self) -> None:
        self.settings = get_settings()
        self.store = ChromaVectorStore()

    # ------------------------------------------------------------------
    # Public API: ingestion
    # ------------------------------------------------------------------

    def ingest_file(self, file_path: str | Path) -> IngestSummary:
        path = Path(file_path).expanduser().resolve()

        try:
            p = pipeline(path)
            chunks = p.process_input_file()
            if not chunks:
                return IngestSummary(
                    files_processed=1,
                    total_chunks=0,
                    errors=[f"{path}: pipeline returned no chunks"]
                )
            return IngestSummary(
                files_processed=1,
                total_chunks=len(chunks),
                errors=[]
            )

        except InvalidMarkdownFileError as e:
            return IngestSummary(files_processed=0, total_chunks=0, errors=[str(e)])

        except Exception as e:
            return IngestSummary(
                files_processed=0,
                total_chunks=0,
                errors=[f"Error ingesting {path}: {e}"],
            )

    def ingest_directory(self, dir_path: str | Path) -> IngestSummary:
        root = Path(dir_path).expanduser().resolve()
        if not root.exists():
            return IngestSummary(0, 0, [f"Directory does not exist: {root}"])
        if not root.is_dir():
            return IngestSummary(0, 0, [f"Path is not a directory: {root}"])

        md_files = sorted(root.rglob("*.md"))

        files_processed = 0
        total_chunks = 0
        errors: List[str] = []

        for md_file in md_files:
            try:
                p = pipeline(md_file)
                chunks = p.process_input_file()
                files_processed += 1

                if chunks:
                    total_chunks += len(chunks)
                else:
                    errors.append(f"{md_file}: returned no chunks")

            except InvalidMarkdownFileError as e:
                errors.append(str(e))

            except Exception as e:
                errors.append(f"{md_file}: {e}")

        return IngestSummary(
            files_processed=files_processed,
            total_chunks=total_chunks,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Public API: querying
    # ------------------------------------------------------------------

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:

        res = self.store.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
        )

        if not res:
            return QueryResult(query=query_text, results=[])

        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]

        results: List[QueryResultChunk] = []
        for doc, meta, dist in zip(docs, metas, dists):
            results.append(
                QueryResultChunk(
                    document=meta.get("document_name", "unknown"),
                    text=doc,
                    score=float(dist),
                    metadata=meta,
                )
            )

        return QueryResult(
            query=query_text,
            results=results,
        )
