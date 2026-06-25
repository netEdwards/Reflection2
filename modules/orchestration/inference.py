


from datetime import datetime
from pydoc import text
import uuid
import certifi
import httpx
from modules.orchestration.message import Message
from openai import OpenAI
from dotenv import load_dotenv
import lmstudio as lms

from modules.orchestration.sql.chatLogStore import ChatLogStore
load_dotenv()

http_client = httpx.Client(verify=certifi.where(), timeout=30.0)

class  ModelInterface:
    def __init__(self, model: str = "qwen2.5-7b-instruct") -> None:
        self.model = lms.llm(model)
        
        
        
    def invoke(self, prompt: str) -> Message:
        """Primitive invokation function to just call the endpoint.

        Args:
            prompt (str): the text or string from the users input prompt.

        Returns:
            Message: The returned Message object containing the endpoints response
        """
        response = self.model.respond(prompt)
        
        text = response.content
        
        return Message(
            id=str(uuid.uuid4()),
            text=text,
            identity="ai",
            timestamp=datetime.now(),
        )
    
    
    def run(self, input: Message) -> Message:
        """Main interface entry point with orchestration. 

        Args:
            input (Message): The users Message from the UX.

        Returns:
            Message: The AI's respsonse.
        """
        msg = input
        if msg.text == "" or msg.text == None:
            print("No message provided")
            return None
        
        chat_logger = ChatLogStore()
        
        chat_logger.add(msg)
        resp = self.invoke(msg.text)
        if isinstance(resp, Message):
            chat_logger.add(resp)
            return resp
        else:
            raise Exception("There was an error in invoking the LLM.")
        
    def run_text(self, input: str) -> Message:
        msg = Message(
            id=str(uuid.uuid4()),
            identity="user",
            text=input,
            timestamp=datetime.now(),
        )