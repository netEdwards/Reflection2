# tests/test_model_interface.py
import os
from pathlib import Path

import pytest

from modules.models.model_interface import LocalQuantModel

###############################################################################
# 1.  Set your model path once, in a way that’s OS‑safe.
#    – We use a raw string literal or Path() to avoid back‑slash escapes.
#    – You can still override from the command line:
#        $ pytest -k model_interface --model_path="D:/models/Mistral‑7B‑GPTQ"
###############################################################################



MODEL_PATH = Path("C:\Reflection\modules\models\Mistral-7B-Instruct-v0.2-GPTQ")

###############################################################################
# 2.  Skip the whole module if the model isn’t present
###############################################################################
if not MODEL_PATH.exists():
    pytest.skip(f"Model not found at {MODEL_PATH}; "
                "run the download script first or pass --model_path=...",
                allow_module_level=True)

###############################################################################
# 3.  Provide the interface once, and close it at the end
###############################################################################
@pytest.fixture(scope="module")
def model():
    print(f"Current path: {str(MODEL_PATH)}")
    m = LocalQuantModel(model_name_or_path=str(MODEL_PATH))
    yield m
    # If your interface exposes a close()/cleanup() call, do it here
    # m.close()

###############################################################################
# 4.  Tests
###############################################################################
def test_generate_output(model):
    prompt = "What is the capital of France?"
    out = model.generate(prompt)
    assert isinstance(out, str) and out.strip(), "No text came back"


