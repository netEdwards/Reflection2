# utils/file_utils.py

import os
from pathlib import Path
from datetime import datetime

def scan_vault(directory: str, extensions=(".md", ".txt")) -> list[Path]:
    """Recursively scans a directory and returns all note files."""
    return [p for p in Path(directory).rglob("*") if p.suffix in extensions]

def read_file(path: Path) -> str:
    """Reads the file content."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_file_metadata(path: Path) -> dict:
    """Returns basic metadata like last modified, size, etc."""
    stat = path.stat()
    return {
        "document_path": str(path),
        "last_modified": datetime.fromtimestamp(stat.st_mtime),
        "created": datetime.fromtimestamp(stat.st_ctime),
        "document_name": path.stem
    }

if __name__ == "__main__":
    vault_path = Path("C:/Mob")
    files = scan_vault(vault_path)
    print(f"Found {len(files)} files.")
    
    for f in files[:20]:
        print(f"File found: {get_file_metadata(f)} \n\n")