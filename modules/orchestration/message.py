
from dataclasses import dataclass
import datetime
import uuid


@dataclass
class Message:
    id: str | None = str(uuid.uuid4())
    text: str | None = None
    identity: str | None = None
    timestamp: datetime.datetime | None = None