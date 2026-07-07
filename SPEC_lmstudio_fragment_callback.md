# Reference: `lmstudio` SDK Fragment Streaming

Status: reference doc, verified against installed SDK version 2026-07-04
Companion doc: `SPEC_streaming_and_thinking.md` (the actual feature this supports)

Everything below was confirmed by reading `.venv/lib/python3.12/site-packages/lmstudio/` directly (`sync_api.py`, `json_api.py`, `_sdk_models/__init__.py`) — not from general knowledge of the package, since SDK details change between versions.

## The short version

`LLM.respond()` — the same method `ModelInterface.invoke()` already calls — accepts an `on_prediction_fragment` callback. Pass one, and it fires once per fragment *while `respond()` is still blocked*, before the full response is ready. You don't need a different method to get streaming; it's a parameter on the one you're already using.

## Signature

```python
def respond(
    self,
    history: Chat | ChatHistoryDataDict | str,
    *,
    response_format: ResponseSchema | None = None,
    config: LlmPredictionConfig | LlmPredictionConfigDict | None = None,
    preset: str | None = None,
    on_message: PredictionMessageCallback | None = None,
    on_first_token: PredictionFirstTokenCallback | None = None,
    on_prediction_fragment: PredictionFragmentCallback | None = None,
    on_prompt_processing_progress: PromptProcessingCallback | None = None,
) -> PredictionResult:
```

(`sync_api.py:1290`)

The one that matters for streaming is `on_prediction_fragment`. The others exist (`on_first_token` fires once, `on_message` fires with assembled messages) but aren't needed for the token-by-token use case.

## The callback type

```python
PredictionFragmentCallback: TypeAlias = Callable[[LlmPredictionFragment], Any]
```

(`json_api.py:1268`) — a plain function taking one `LlmPredictionFragment` argument. Return value is ignored (`Any`, not used for control flow — you can't stop generation by returning something from here).

## `LlmPredictionFragment` fields

```python
class LlmPredictionFragment:
    content: str                                        # the text delta for this fragment
    tokens_count: int                                    # field name "tokensCount" in raw API
    contains_drafted: bool                                # speculative-decoding related, ignore for this use case
    reasoning_type: LlmPredictionFragmentReasoningType    # field name "reasoningType" in raw API
```

(`_sdk_models/__init__.py:1253`)

`reasoning_type` is the field that matters for splitting thinking vs. answer text:

```python
LlmPredictionFragmentReasoningType = Literal[
    "none", "reasoning", "reasoningStartTag", "reasoningEndTag"
]
```

(`_sdk_models/__init__.py:1248`) — `"reasoning"` fragments are inside the `<think>` block, `"none"` fragments are the real answer, and the `Tag` variants mark the transition fragments themselves (the literal `<think>`/`</think>` boundary tokens). This tagging only works because `reasoningParsing` is passed in `config` (see below) — without it, every fragment comes back as `"none"` and you're back to raw undifferentiated text.

## The config that makes reasoning_type actually work

This is already in `inference.py`'s `invoke()` from the earlier crash fix — the same config is required for fragment tagging to function, not just for avoiding the parser crash:

```python
config={
    "reasoningParsing": {
        "enabled": True,
        "startString": "<think>",
        "endString": "</think>",
    }
}
```

If this is missing, `on_prediction_fragment` still fires per-fragment, but `reasoning_type` will just be `"none"` throughout — you'd be back to manually string-matching `<think>` yourself.

## What you get back once `respond()` finally unblocks

```python
class PredictionResult:
    content: str                    # full assembled text (same as today's response.content)
    parsed: AnyPrediction            # only relevant for structured/JSON output, not used here
    stats: LlmPredictionStats        # token counts, timing — not currently used anywhere in the codebase
    model_info: LlmInfo
    load_config: LlmLoadModelConfig
    prediction_config: LlmPredictionConfig
```

(`json_api.py:474`) — this is unchanged from what `invoke()` already reads today (`response.content`). Streaming doesn't change the final return value at all, only what happens *during* the call via the callback.

## Minimal isolated example (confirm the mechanics before touching the real app)

```python
import lmstudio as lms

def on_fragment(fragment):
    tag = fragment.reasoning_type
    print(f"[{tag}] {fragment.content!r}")

model = lms.llm("qwen3-4b")
result = model.respond(
    "Explain photosynthesis in two sentences.",
    config={
        "reasoningParsing": {
            "enabled": True,
            "startString": "<think>",
            "endString": "</think>",
        }
    },
    on_prediction_fragment=on_fragment,
)
print("FINAL:", result.content)
```

Running something like this standalone (outside the app entirely) is the fastest way to see the fragment cadence and reasoning_type transitions before wiring it into `ModelInterface`, `JsApi`, and `chat.tsx`.

## Note on threading

The callback almost certainly fires from a background thread the SDK manages internally (its websocket connection to the LM Studio server), not whatever thread called `.respond()`. This matters once you get to pushing fragments into the pywebview window (see the companion spec's section 5) — confirm whether `window.evaluate_js()` is safe to call from inside this callback's thread before building UI around it.
