from typing import List, Optional, Dict, Any
from pydantic import Field, PrivateAttr
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

class ChatQuantModel(BaseChatModel):
    """
    LangChain-compatible wrapper for a quantized chat model using auto-gptq.
    """

    model_id: str = Field(default="TheBloke/openchat-3.5-0106-GPTQ", description="HuggingFace repo ID or local path to quantized model")
    device: str = Field(default="cuda")
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)

    _tokenizer: Any = PrivateAttr()
    _model: Any = PrivateAttr()
    _eos_token_id: Optional[int] = PrivateAttr(default=None)
    _pad_token_id: Optional[int] = PrivateAttr(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_model()

    @property
    def _llm_type(self) -> str:
        return "chat-quant"

    def _load_model(self):
        import torch
        from transformers import AutoTokenizer
        from auto_gptq import AutoGPTQForCausalLM

        print(f"🔄 Loading tokenizer from {self.model_id}")
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)

        self._tokenizer.pad_token = self._tokenizer.eos_token
        self._pad_token_id = self._tokenizer.pad_token_id
        self._eos_token_id = self._tokenizer.convert_tokens_to_ids("<|endofconversation|>")

        print(f"🔄 Loading quantized model from {self.model_id}")
        self._model = AutoGPTQForCausalLM.from_quantized(
            self.model_id,
            device_map="auto" if self.device == "cuda" else None,
            torch_dtype=torch.float16,
            use_safetensors=True,
            trust_remote_code=True
        ).to(self.device).eval()

        # Default gen args if not set
        self.model_kwargs.setdefault("eos_token_id", self._eos_token_id)
        self.model_kwargs.setdefault("pad_token_id", self._pad_token_id)
        if self.model_kwargs.get("temperature") or self.model_kwargs.get("top_p"):
            self.model_kwargs.setdefault("do_sample", True)

    def _format_messages(self, messages: List[BaseMessage]) -> str:
        output = ""
        for msg in messages:
            if isinstance(msg, SystemMessage):
                output += f"<|system|>\n{msg.content.strip()}\n"
            elif isinstance(msg, HumanMessage):
                output += f"<|user|>\n{msg.content.strip()}\n"
            elif isinstance(msg, AIMessage):
                output += f"<|assistant|>\n{msg.content.strip()}\n"
        return output + "<|assistant|>\n"

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        import torch

        prompt = self._format_messages(messages)
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self.device)

        generation_args = {**self.model_kwargs, **kwargs}
        generation_args.setdefault("eos_token_id", self._eos_token_id)

        with torch.no_grad():
            output = self._model.generate(**inputs, **generation_args)

        decoded = self._tokenizer.decode(output[0], skip_special_tokens=True)
        response = decoded.split("<|assistant|>\n")[-1].strip()
        response = response.split("<|endofconversation|>")[0].strip()

        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response))])

    async def _agenerate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        return self._generate(messages, stop=stop, **kwargs)
