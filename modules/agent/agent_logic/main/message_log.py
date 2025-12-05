from ast import List
from datetime import datetime
import sqlite3
from typing import Iterable, Literal
import uuid

from attr import dataclass
from modules.agent.agent_settings import get_agent_settings


@dataclass
class MessageRecord:
    id: str
    role: Literal["user", "assistant", "system"]
    text: str
    created_at: datetime

class MessageLog:
    """
    Local SQLite-backed log of all messages between user and agent. This is the append-only "life-log" of the history. 
    NOT semantics. 
    
    """
    
    def __init__(self) -> None:
        cfg = get_agent_settings()
        self.db_path = cfg.sql_dir
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        self._init_schema()
        
    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_messsages_role ON messages(role);")
        self.conn.commit()
        
    def append(self, message: MessageRecord) -> MessageRecord:
        """Insert a MessageRecord into the log
        params:
        - message: MessageRecord
        returns:
        - MessageRecord
        """
        if not message.id:
            message.id = str(uuid.uuid4())
        
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO messages (id, role, text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                message.id,
                message.role,
                message.text,
                message.created_at.isoformat(),
            ),
        )
        self.conn.commit()
        return message
    
    def log_user(self, text: str) -> MessageRecord:
        """Convenience: create+persist a user message"""
        msg = MessageRecord(
            id=str(uuid.uuid4()),
            role="user",
            text=text,
            created_at=datetime.now(),
        )
        return self.append(msg)
    def log_assistant(self, text: str) -> MessageRecord:
        msg = MessageRecord(
            id=str(uuid.uuid4()),
            role="assistant",
            text=text,
            created_at=datetime.now(),
        )
        return self.append(msg)
    def get_recent(self, limit: int = 50) -> List[MessageRecord]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, role, text, created_at
            FROM messages
            ORDER BY datetime(create_at) DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return [self._row_to_messae(r) for r in rows]
    
    def get_by_ids(
        self,
        ids: Iterable[str]
    )-> List[MessageRecord]:
        ids = list(ids)
        if not ids:
            return []
        
        placeholders = ",".join("?" for _ in ids)
        sql = f"""
            SELECT id, role, text, created_at
            FROM messages
            WHERE id IN ({placeholders})
            ORDER BY datetime(created_at) ASC
        """
        cur = self.conn.cursor()
        cur.execute(sql, ids)
        rows = cur.fetchall()
        return [self._row_to_message(r) for r in rows]
    
    def get_between(
        self,
        start: datetime,
        end: datetime,
    ) -> List[MessageRecord]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, role, text, created_at
            FROM messages
            WHERE datetime(created_at) >= ? AND datetime(created_at) <= ?
            ORDER BY datetime(created_at) ASC
            """,
            (start.isoformat(), end.isoformat()),
        )
        rows = cur.fetchall()
        return [self._row_to_message(r) for r in rows]

    # ---------- Housekeeping ----------

    def delete_all(self) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM messages;")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
    
    @staticmethod
    def _row_to_message(row: sqlite3.Row) -> MessageRecord:
        return MessageRecord(
            id=row["id"],
            role=row["role"],
            text=row["text"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )