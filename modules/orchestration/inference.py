from datetime import datetime
import uuid
from modules.orchestration.message import Message
from dotenv import load_dotenv
import lmstudio as lms

from modules.orchestration.sql.chatLogStore import ChatLogStore
from modules.orchestration.orc_settings import get_settings
from modules.vectors.VectorService import VectorService
load_dotenv()

class ModelInterface:
    def __init__(self, model: str | None = None, on_fragment = None) -> None:
        self.model = lms.llm(model or get_settings().default_model)
        self.vectors = VectorService()
        self.on_fragment = on_fragment
        
        
        
    def invoke(self, prompt: str) -> Message:
        """Primitive invokation function to just call the endpoint.

        Args:
            prompt (str): the text or string from the users input prompt.

        Returns:
            Message: The returned Message object containing the endpoints response
        """
        # Qwen3 (and other reasoning models) emit <think> blocks. Without telling
        # LM Studio how to parse them, its server tries to validate the raw,
        # still-open <think> text as plain content mid-stream and throws:
        # "The model produced output that does not match the expected Content-only format".

        

        # Local stream receiver. Forwards both reasoning and answer fragments so the UI
        # can show thinking-in-progress — only the literal <think>/</think> boundary
        # marker fragments are dropped, since their content is just the tag text itself.
        def _on_fragment_recieved(fragment: lms.LlmPredictionFragment):
            if not fragment or fragment.reasoning_type in ("reasoningStartTag", "reasoningEndTag"):
                return
            if self.on_fragment is not None:
                self.on_fragment({
                    "content": fragment.content,
                    "reasoning_type": fragment.reasoning_type,
                })

        response = self.model.respond(
            prompt,
            config={
                "reasoningParsing": {
                    "enabled": True,
                    "startString": "<think>",
                    "endString": "</think>",
                }
            },
            on_prediction_fragment=_on_fragment_recieved,
        )

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
        prompt = self._build_rag_prompt(msg.text)
        resp = self.invoke(prompt)
        if isinstance(resp, Message):
            chat_logger.add(resp)
            return resp
        else:
            raise Exception("There was an error in invoking the LLM.")
        
    def _build_rag_prompt(self, user_text: str, n_results: int = 5) -> str:
        """Retrieve relevant note chunks and fold them into the prompt sent to the model.

        Falls back to the raw user text if retrieval fails or the store is empty/unindexed,
        so chat still works before anything has been ingested.
        """
        try:
            result = self.vectors.query(user_text, n_results=n_results)
        except Exception as e:
            print(f"RAG retrieval failed, falling back to raw prompt: {e}")
            return user_text

        if not result.results:
            return user_text

        context_blocks = []
        for i, chunk in enumerate(result.results, start=1):
            heading = (chunk.metadata or {}).get("heading_path")
            source = chunk.document + (f" ({heading})" if heading else "")
            context_blocks.append(f"[{i}] {source}:\n{chunk.text}")

        context = "\n\n".join(context_blocks)

        return (
            "You are a helpful assistant answering questions using the user's personal notes.\n"
            "Use the following context from the user's notes if it's relevant. "
            "If it isn't relevant, answer normally and don't mention the context.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {user_text}"
        )

    def run_text(self, input: str) -> Message:
        msg = Message(
            id=str(uuid.uuid4()),
            identity="user",
            text=input,
            timestamp=datetime.now(),
        )
        return self.run(msg)