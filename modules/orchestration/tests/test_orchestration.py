# test_orchestration.py
from datetime import datetime
from modules.orchestration.inference import ModelInterface
from modules.orchestration.message import Message



def test_run(temp_chat_db):
    interface = ModelInterface()
    msg = Message(id="012", identity="user", text="Hello!", timestamp=datetime.now())
    response = interface.run(input=msg)

    if isinstance(response, Message):
        print("Message received:", response.text)
    else:
        raise RuntimeError("Invalid response type")