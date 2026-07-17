import datetime
import sqlite3
import uuid
from dataclasses import dataclass, field

from ..orc_settings import OrchestrationSettings, get_settings


@dataclass
class Message:
    thread_id: str
    id: str | None = field(default_factory=lambda: str(uuid.uuid4()))
    text: str | None = None
    identity: str | None = None
    timestamp: datetime.datetime | None = None


@dataclass
class Thread:
    id: str | None = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Chat"
    created_at: str | None = field(default_factory=lambda: datetime.datetime.now().isoformat())


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
        base = f"Message field '{self.field}' is null or invalid"
        if self.msg_id:
            return f"{base} (msg_id={self.msg_id})"
        return base

class ChatLogStore:
    def __init__(self):
        self.settings = get_settings()
        self.db_path = self.settings.chat_db_path
        self.msg_table_name = self.settings.messages_table_name
        self.threads_table_name = self.settings.threads_table_name
        print(f"db_path: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=5)

        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")
        self.conn.execute("PRAGMA foreign_keys = ON;")

        self._init_schema()

    def _init_schema(self):
        with self.conn:
            # threads must exist before messages, which references it via FK.
            self.conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.threads_table_name} (
                        id TEXT PRIMARY KEY NOT NULL,
                        title TEXT,
                        created_at TEXT NOT NULL
                    );
            """)

            self.conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.msg_table_name} (
                        id TEXT PRIMARY KEY NOT NULL,
                        thread_id TEXT NOT NULL REFERENCES {self.threads_table_name}(id) ON DELETE CASCADE,
                        identity TEXT NOT NULL,
                        text TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    );
            """)

            # Serves list_messages()'s "WHERE thread_id = ? ORDER BY timestamp" query directly.
            self.conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.msg_table_name}_thread_time
                    ON {self.msg_table_name} (thread_id, timestamp);
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

        if message.thread_id is None:
            raise NullMessageValuesError("thread_id", message.id)

        if message.identity is None or message.identity.strip() == "":
            raise NullMessageValuesError("identity", message.id)

        if message.text is None or message.text.strip() == "":
            raise NullMessageValuesError("text", message.id)

        if message.timestamp is None:
            raise NullMessageValuesError("timestamp", message.id)

    def add_message(self, message: Message = None):
        """Add a single `Message` to the messages table.

        Args:
            message (Message, optional): Message object with non null fields. Defaults to None.
        """
        self._validate_message(message)
        timestamp = (
            message.timestamp.isoformat()
            if isinstance(message.timestamp, datetime.datetime)
            else message.timestamp
        )
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                f"INSERT INTO {self.msg_table_name} (id, thread_id, text, identity, timestamp) VALUES (?, ?, ?, ?, ?)",
                (message.id, message.thread_id, message.text, message.identity, timestamp)
                )

    def remove_message(self, msg_id: str) -> bool:
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(f"""
                        DELETE FROM {self.msg_table_name} WHERE id = ?
                        """, (msg_id,),
                        )
        return cur.rowcount > 0

    def list_messages(self, thread_id: str, t_from: str | None = None, t_to: str | None = None) -> list[Message]:
        """List a single thread's messages ordered by timestamp, optionally bounded by an ISO datetime range.

        Args:
            thread_id (str): Only messages belonging to this thread are returned.
            t_from (str | None): ISO format datetime lower bound (inclusive). None means unbounded.
            t_to (str | None): ISO format datetime upper bound (inclusive). None means unbounded.

        Returns:
            list[Message]: Messages ordered oldest to newest.
        """
        clauses = ["thread_id = ?"]
        params: list[str] = [thread_id]
        if t_from is not None:
            clauses.append("timestamp >= ?")
            params.append(t_from)
        if t_to is not None:
            clauses.append("timestamp <= ?")
            params.append(t_to)

        where = f"WHERE {' AND '.join(clauses)}"

        cur = self.conn.cursor()
        cur.execute(
            f"""
            SELECT id, thread_id, identity, text, timestamp
            FROM {self.msg_table_name}
            {where}
            ORDER BY timestamp ASC;
            """,
            params,
        )
        return [
            Message(
                id=row["id"],
                thread_id=row["thread_id"],
                identity=row["identity"],
                text=row["text"],
                timestamp=row["timestamp"],
            )
            for row in cur.fetchall()
        ]

    def get_message(self, msg_id: str) -> Message | None:
        cur = self.conn.cursor()
        cur.execute(f"""
                    SELECT id, thread_id, identity, text, timestamp
                    FROM {self.msg_table_name}
                    WHERE id = ?
                    LIMIT 1;
                    """, (msg_id,),)
        row = cur.fetchone()
        if row is None:
            return None
        return Message(
            id=row["id"],
            thread_id=row["thread_id"],
            identity=row["identity"],
            text=row["text"],
            timestamp=row["timestamp"],
        )

    def create_thread(self, title: str = "New Chat", created_at: str | None = None) -> str:
        """
        Create/Add a new thread to the threads table. Creates an ID and returns it.

        Args:
            title (str): Display name of the thread. Defaults to "New Chat".
            created_at (str | None): Optional ISO format timestamp. Generated automatically if absent.

        Returns:
            str: id of the created thread.
        """
        thread = Thread(title=title) if created_at is None else Thread(title=title, created_at=created_at)

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                f"INSERT INTO {self.threads_table_name} (id, title, created_at) VALUES (?, ?, ?)",
                (thread.id, thread.title, thread.created_at),
            )

        return thread.id

    def remove_thread(self, thread_id: str) -> bool:
        """
        Removes a thread from the threads table. Its messages are cascade-deleted
        (ON DELETE CASCADE on messages.thread_id).

        Args:
            thread_id (str): the id of the thread to be deleted.

        Returns:
            bool: True if a thread was deleted, False if no thread matched.
        """
        if not thread_id:
            return False

        with self.conn:
            cur = self.conn.cursor()
            cur.execute(
                f"DELETE FROM {self.threads_table_name} WHERE id = ?",
                (thread_id,),
            )

        return cur.rowcount > 0

    def get_thread(self, thread_id: str) -> Thread | None:
        """Look up a single thread by id.

        Args:
            thread_id (str): id of the thread to fetch.

        Returns:
            Thread | None: the thread, or None if no thread matches.
        """
        cur = self.conn.cursor()
        cur.execute(f"""
                    SELECT id, title, created_at
                    FROM {self.threads_table_name}
                    WHERE id = ?
                    LIMIT 1;
                    """, (thread_id,),)
        row = cur.fetchone()
        if row is None:
            return None
        return Thread(id=row["id"], title=row["title"], created_at=row["created_at"])

    def list_threads(self, t_from: str | None = None, t_to: str | None = None) -> list[Thread]:
        """List all threads ordered oldest to newest, optionally bounded by an ISO datetime
        range on creation time.

        Args:
            t_from (str | None): ISO format datetime lower bound (inclusive) on created_at. None means unbounded.
            t_to (str | None): ISO format datetime upper bound (inclusive) on created_at. None means unbounded.

        Returns:
            list[Thread]: Threads ordered oldest to newest.
        """
        clauses = []
        params: list[str] = []
        if t_from is not None:
            clauses.append("created_at >= ?")
            params.append(t_from)
        if t_to is not None:
            clauses.append("created_at <= ?")
            params.append(t_to)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        cur = self.conn.cursor()
        cur.execute(
            f"""
            SELECT id, title, created_at
            FROM {self.threads_table_name}
            {where}
            ORDER BY created_at ASC;
            """,
            params,
        )
        return [
            Thread(id=row["id"], title=row["title"], created_at=row["created_at"])
            for row in cur.fetchall()
        ]
