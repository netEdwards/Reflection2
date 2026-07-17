
import pytest

from modules.orchestration.orc_settings import get_settings


@pytest.fixture
def temp_chat_db(monkeypatch, tmp_path):
    db = tmp_path / "chats.sqlite"
    monkeypatch.setenv("REFLECTION_CHAT_DB_PATH", str(db))
    get_settings.cache_clear()
    return db