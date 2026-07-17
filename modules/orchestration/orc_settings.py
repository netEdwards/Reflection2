# modules/orchestration/settings.py
from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

APP_NAME = "reflection_etl"  # keep this consistent across the whole app


def _default_base_data_dir() -> Path:
    """
    Cross-platform default data dir.

    Windows: %LOCALAPPDATA%/reflection
    macOS:   ~/Library/Application Support/reflection
    Linux:   ~/.local/share/reflection
    """
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        root = Path(os.getenv("LOCALAPPDATA", home / "AppData" / "Local"))
    elif system == "Darwin":
        root = Path(os.getenv("XDG_DATA_HOME", home / "Library" / "Application Support"))
    else:
        root = Path(os.getenv("XDG_DATA_HOME", home / ".local" / "share"))

    return root / APP_NAME 


def _load_file_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@dataclass(frozen=True)
class OrchestrationSettings:
    base_data_dir: Path
    sql_dir: Path
    chat_db_path: Path

    default_model: str
    request_timeout_s: float
    
    messages_table_name: str
    threads_table_name: str

    @property
    def config_path(self) -> Path:
        return self.base_data_dir / "config.json"


@lru_cache()
def get_settings() -> OrchestrationSettings:
    # 1) Base dir shared across app
    base_data_dir_env = os.getenv("REFLECTION_DATA_DIR")
    base_data_dir = Path(base_data_dir_env) if base_data_dir_env else _default_base_data_dir()
    base_data_dir.mkdir(parents=True, exist_ok=True)

    # 2) Optional config file
    file_cfg = _load_file_config(base_data_dir / "config.json")

    def cfg(key: str, default: Any) -> Any:
        """
        Env var wins, then config file, then default.
        Orchestration settings use REFLECTION_* keys too, so you have one config surface.
        """
        env_key = f"REFLECTION_{key}"
        if env_key in os.environ:
            return os.environ[env_key]
        if key in file_cfg:
            return file_cfg[key]
        return default

    # 3) Defaults
    sql_dir = Path(cfg("SQL_DIR", base_data_dir / "sql"))
    sql_dir.mkdir(parents=True, exist_ok=True)

    chat_db_path = Path(cfg("CHAT_DB_PATH", sql_dir / "chats.sqlite"))

    default_model = str(cfg("DEFAULT_MODEL", "qwen3-4b"))
    request_timeout_s = float(cfg("REQUEST_TIMEOUT_S", 30.0))
    
    messages_table_name = str(cfg("MSG_TABLE_NAME", "messages"))
    threads_table_name = str(cfg("THREADS_TABLE_NAME", "threads"))

    return OrchestrationSettings(
        base_data_dir=base_data_dir,
        sql_dir=sql_dir,
        chat_db_path=chat_db_path,
        default_model=default_model,
        request_timeout_s=request_timeout_s,
        messages_table_name=messages_table_name,
        threads_table_name=threads_table_name
    )
