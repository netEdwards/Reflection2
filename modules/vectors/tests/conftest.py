from pathlib import Path
import pandas as pd
import pytest

# Normal imports — assume parser.py and chunker.py live in your root or package
from modules.vectors.components.parser import MarkdownNoteParser
from modules.vectors.components.chunker import chunk_elements


VAULT_PATH = Path(r"C:\Mob\test_note")
ARTIFACTS_DIR = Path("./artifacts").resolve()
RECON_DIR = ARTIFACTS_DIR / "reconstructed"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
RECON_DIR.mkdir(parents=True, exist_ok=True)


@pytest.mark.skipif(not VAULT_PATH.exists(), reason="Vault path does not exist")
def test_chunk_vault_to_dataframe():
    parser = MarkdownNoteParser()

    all_rows = []
    for md_path in sorted(VAULT_PATH.rglob("*.md")):
        elements = parser.parse_markdown_file(md_path)
        chunks = chunk_elements(
            elements,
            doc_name=md_path.name,
            doc_path=str(md_path),
            max_tokens=900,
            overlap=150,
        )
    assert chunks is not None
    df = pd.DataFrame(all_rows).sort_values(["file", "index"]).reset_index(drop=True)
    
    assert not df.empty
    assert df["tokens"].max() <= 900

    print(f"\nVault: {VAULT_PATH}")
    print(f"Chunks: {len(df)}")
    print(f"CSV saved to {ARTIFACTS_DIR / 'chunks.csv'}")
    print(f"Reconstructions saved to {RECON_DIR}")
    
    return df
