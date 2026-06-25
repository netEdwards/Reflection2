from datetime import datetime
import uuid
import pytest
from modules.orchestration.message import Message
from modules.orchestration.sql.chatLogStore import ChatLogStore


def test_sql_add(temp_chat_db):
    sql = ChatLogStore()
    msg_id = str(uuid.uuid4())
    test_msg = Message(
        id = msg_id,
        text = "Hello!",
        identity="user",
        timestamp=datetime.now(),
    )
    sql.add(test_msg)
    msg = sql.get(msg_id)
    assert msg is not None
    assert msg.id == msg_id
    if msg:
        sql.remove(msg.id)
        print("msg removed")
        r_msg = sql.get(msg.id)
        assert r_msg is None
        
    sql.close()
    