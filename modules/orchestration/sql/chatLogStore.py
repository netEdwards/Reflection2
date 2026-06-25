from calendar import c
import sqlite3
from modules.orchestration.message import Message
from ..orc_settings import OrchestrationSettings, get_settings

class NullMessageValuesError (Exception):
    """Raised when on or more values in `Message` is null or invalid. This is a violation of persistance constraints.

    Args:
        Exception (NullMessageValuesError): Simple error thrown on null or invalid message values.
    """
    def __init__(self, field: str, msg_id: str | None = None):
        self.field = field
        self.msg_id = msg_id
        super().__init__(self._build_message())
        
    def _build_message(self) -> str:
        base = f"Message field '{self.field} is null or invalid"
        if self.msg_id:
            return f"{base} (msg_id={self.msg_id})"

class ChatLogStore:
    def __init__(self):
        self.settings = get_settings()
        self.db_path = self.settings.chat_db_path
        self.table = self.settings.messages_table_name
        print(f"db_path: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=5)
        
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        
        self._init_schema()
        
    def _init_schema(self):
        with self.conn:
            self.conn.execute(f"""
                              CREATE TABLE IF NOT EXISTS {self.table} (
                                  id TEXT NOT NULL,
                                  identity TEXT NOT NULL,
                                  text TEXT NOT NULL,
                                  timestamp TEXT NOT NULL
                              );
                              """)
            self.conn.execute(f"""
                              CREATE INDEX IF NOT EXISTS idx_{self.table}_chat_time
                              ON {self.table} (id, timestamp);
                              """)
            
    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
            
    def _validate_message(self, message: Message) -> None:
        """Valides the fields of a message, upon invalid or null field `NullMessageValueError is raised.

        Args:
            message (Message): Message object with possibly invalid fields.

        Raises:
            NullMessageValuesError: if any field is invalid or null.
        """
        if message.id is None:
            raise NullMessageValuesError("id")

        if message.identity is None or message.identity.strip() == "":
            raise NullMessageValuesError("identity", message.id)

        if message.text is None or message.text.strip() == "":
            raise NullMessageValuesError("text", message.id)

        if message.timestamp is None:
            raise NullMessageValuesError("timestamp", message.id)
    
    def add(self, message: Message = None):
        """Add a single `Message` to the messages table.

        Args:
            message (Message, optional): Message object with non null fields. Defaults to None.
        """
        self._validate_message(message)
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                f"INSERT INTO {self.table} (id, text, identity, timestamp) VALUES (?, ?, ?, ?)",
                (message.id, message.text, message.identity, message.timestamp)
                )
        
    def remove(self, msg_id: str):
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(f"""
                        DELETE FROM {self.table} WHERE id = ?
                        """, (msg_id,),
                        )
        return cur.rowcount > 0
    
    def get(self, msg_id: str) -> Message | None:
        cur = self.conn.cursor()
        cur.execute(f"""
                    SELECT id, identity, text, timestamp
                    FROM {self.table}
                    WHERE id = ?
                    LIMIT 1;
                    """, (msg_id,),)
        row = cur.fetchone()
        if row is None:
            return None
        return Message(
            id=row["id"],
            identity=row["identity"],
            text=row["text"],
            timestamp=row["timestamp"],
        )