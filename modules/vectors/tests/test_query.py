import pytest

from modules.vectors.index.chroma_store import ChromaVectorStore
from dotenv import load_dotenv
load_dotenv()


def test_chroma_query():
    store = ChromaVectorStore(
        collection_name="reflection_notes",
        persist_directory="./.chroma"
    )
    
    if not store:
        pytest.fail("Chroma store was not initialized properly.")

    query_text = ["Light"]

    results = store.query(
        query_texts=query_text,
        n_results=2
    )
    
    assert results is not None, "Query results are None."
    print("TEST: Query executed successfully. Results:")
    print(results)
    