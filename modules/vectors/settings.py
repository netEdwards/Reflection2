
import os
import json
import platform
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


APP_NAME = "reflection_etl"

def _default_base_data_dir() -> Path:
    """Cross-platform default data dir for reflection_etl

    - Windows: %APPDATA%/Reflection
    - macOS: ~/Library/Application Support/Reflection
    - Linux: ~/.local/share/reflection
    """
    system = platform.system()
    home = Path.home()
    
    if system == "Windows":
        root = Path(os.getenv("LOCALAPPDATA", home / "AppData" / "Local"))
    elif system == "Darwin":
        root = Path(os.getenv("XDG_DATA_HOME", home / "Library" / "Application Support"))
    else:  # Linux / everything else
        root = Path(os.getenv("XDG_DATA_HOME", home / ".local" / "share"))

    return root / APP_NAME



@dataclass(frozen=True)
class VectorsSettings:
    base_data_dir: Path
    chroma_dir: Path
    default_collection_name: str
    
    openai_embedding_model: str
    openai_embedding_batch_size: int
    
    @property
    def config_path(self) -> Path:
        return self.base_data_dir / "config.json"
    
def _load_file_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # don't let a bad config file kill the app
        return {}
    
    
@lru_cache()
def get_settings() -> VectorsSettings:
    """
    Load settings with the following precedence:

    1. Environment variables (REFLECTION_*)
    2. config.json in the base data dir (if present)
    3. Hard-coded defaults
    """
    # 1. Base data dir (where *all* Reflection data lives)
    base_data_dir_env = os.getenv("REFLECTION_DATA_DIR")
    base_data_dir = Path(base_data_dir_env) if base_data_dir_env else _default_base_data_dir()
    base_data_dir.mkdir(parents=True, exist_ok=True)

    # 2. Optional config file
    file_cfg = _load_file_config(base_data_dir / "config.json")

    def cfg(key: str, default: Any) -> Any:
        """Helper: env var wins, then config file, then default."""
        env_key = f"REFLECTION_{key}"
        if env_key in os.environ:
            return os.environ[env_key]
        if key in file_cfg:
            return file_cfg[key]
        return default

    chroma_dir = Path(cfg("CHROMA_DIR", base_data_dir / "chroma"))
    chroma_dir.mkdir(parents=True, exist_ok=True)

    collection_name = cfg("CHROMA_COLLECTION", "reflection_notes")

    emb_model = cfg("EMBEDDING_MODEL", "text-embedding-3-small")
    emb_batch = int(cfg("EMBEDDING_BATCH_SIZE", 64))

    return VectorsSettings(
        base_data_dir=base_data_dir,
        chroma_dir=chroma_dir,
        default_collection_name=collection_name,
        openai_embedding_model=emb_model,
        openai_embedding_batch_size=emb_batch,
    )