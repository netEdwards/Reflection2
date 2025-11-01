"""
Factory that gives a *single* LCQuantModel instance.
Keeps heavyweight model load outside the graph builder.
"""
from pathlib import Path
from typing import Optional, Dict, Any

from modules.models.model_interface import ChatQuantModel


model_config_1 = ChatQuantModel(
    model_id="TheBloke/openchat-3.5-0106-GPTQ",
    device="cuda",
    model_kwargs={
        "max_new_tokens": 500,
        "temperature": 0.1,
        "top_p": 0.7,
        "do_sample": True,  # optional, auto-added if top_p/temp exists
        "repetition_penalty": 1.4
    }
)
