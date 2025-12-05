import os
import json
import platform
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


APP_NAME = "reflection_etl";

def _default_base_data_dir() -> Path:
    """Cross-platform default data dir for Reflection.

    - Windows: %LOCALAPPDATA%/reflection_etl
    - macOS:   ~/Library/Application Support/reflection_etl
    - Linux:   ~/.local/share/reflection_etl
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
class AgentSettings:
    base_data_dir: Path
    message_db_path: Path
    memory_collection_name: str
    max_bootstrap_recent_messages: int
    default_memory_importance: float
    @property
    def config_path(self) -> Path:
        """Shared config.json (same as vectors), for cross-component config."""
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
def get_agent_settings() -> AgentSettings:
    """
    Load agent-specific settings with the following precedence:

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
    
    sql_dir = base_data_dir / "sql"

    # SQLite message log location
    message_db_path = Path(cfg("MESSAGE_DB_PATH", sql_dir / "messages.sqlite3"))
    message_db_path.parent.mkdir(parents=True, exist_ok=True)

    # Chroma collection name for agent memories
    memory_collection_name = cfg("MEMORY_COLLECTION", "reflection_memories")
    max_bootstrap_recent_messages = int(cfg("AGENT_BOOTSTRAP_RECENT_MESSAGES", 40))
    default_memory_importance = float(cfg("DEFAULT_MEMORY_IMPORTANCE", 0.5))

    return AgentSettings(
        base_data_dir=base_data_dir,
        sql_dir=sql_dir, #root for sql in this library
        message_db_path=message_db_path,
        memory_collection_name=memory_collection_name,
        max_bootstrap_recent_messages=max_bootstrap_recent_messages,
        default_memory_importance=default_memory_importance,
    )
    