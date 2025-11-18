# modules/vectors/tests/test_pipeline_embedding.py

from pathlib import Path
import os
import pytest
from dotenv import load_dotenv
load_dotenv()

from modules.vectors.main_pipeline import pipeline


@pytest.mark.skipif(
    "OPENAI_KEY" not in os.environ,
    reason="Requires OPENAI_KEY to call OpenAI embeddings",
)
def test_pipeline_adds_embeddings():
    # 1) create a tiny markdown file in a temp dir
    _dir = Path(__file__).parent
    md_path: Path = _dir / "artifacts" / "test_md.md"

    # 2) run the pipeline
    pipe = pipeline(md_path)
    df = pipe.process_input_file()

    # 3) basic checks
    assert df is not None
    assert not df.empty

    # chunk metadata columns
    for col in ("text", "document_name", "document_path"):
        assert col in df.columns

    # 4) embeddings column exists and aligns
    assert "embeddings" in df.columns
    assert len(df["embeddings"]) == len(df["text"])

    # 5) embeddings look like vectors of floats
    first_vec = df["embeddings"].iloc[0]
    assert isinstance(first_vec, list)
    assert len(first_vec) > 0
    assert isinstance(first_vec[0], float)
