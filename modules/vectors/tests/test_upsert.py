from turtle import st
import pytest
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from modules.vectors.components.parser import MarkdownNoteParser
from modules.vectors.index.chroma_store import ChromaVectorStore


def test_pipeline_to_upsert():
    test_path = Path(__file__).parent / "artifacts" / "test_md.md"
    
    parser = MarkdownNoteParser()
    
    parsed_md = parser.parse_markdown_file(path=test_path)
    
    assert parsed_md is not None, "Parsed markdown DataFrame is None."
    assert not len(parsed_md) == 0, "Parsed markdown DataFrame is empty."
    
    store = ChromaVectorStore(
        collection_name="reflection_notes",
        persist_directory="./.chroma"
    )
    
    if not store.collection:
        pytest.fail("Chroma collection was not created properly.")

    assert store.collection.name == "reflection_notes", "Chroma collection name mismatch."
    
    print("TEST: Executing query on note...")
    
    results = store.query(
        query_texts=["What is Light?"],
        n_results=2
    )
    
    assert results is not None, "Query results are None."
    print("TEST: Query executed successfully. Results:")
    print(results)
