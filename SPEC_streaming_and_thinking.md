# Spec: Streaming Chat Responses + Visible Thinking Text

Status: proposed, not started
Author: drafted by Claude at Adrian's request, 2026-07-04
Companion doc: `SPEC_lmstudio_fragment_callback.md` (SDK mechanics reference)

## 1. Problem

Two related complaints from actually using the chat right now:

1. **No visibility into reasoning.** Qwen3 emits a `<think>...</think>` block before its real answer. Right now `chat.tsx`'s `stripThinking()` deletes it entirely before display — so today you can't see it in the app at all, only by digging through raw Python output or LM Studio's server log. Deleting it was a reasonable stopgap to get chat working, but the goal now is to show it in a way that isn't painful to read (i.e. not just a raw undifferentiated wall of text mixed with the answer) — something collapsible/visually distinct, closer to how ChatGPT/Claude present a "thought for N seconds" section.
2. **No streaming.** `send_chat` currently blocks until the *entire* response (thinking + answer) is generated, then returns it all at once. For a 4B model doing visible reasoning, that can be several seconds to tens of seconds of a frozen UI with no feedback. Token-by-token streaming would show the user something is happening immediately.

These two are bundled into one spec because **they share the same plumbing**. Once you're streaming fragments instead of waiting for one final string, you get thinking-vs-answer separation almost for free — see section 3.

## 2. Why bundle them

LM Studio's own SDK (via the `reasoningParsing` config already wired into `ModelInterface.invoke()` for the crash fix) tags every streamed fragment with whether it's reasoning or regular content. That means:

- If you build the *streaming* path fragment-by-fragment, you already have the reasoning/content split for free per fragment — no client-side regex needed to find `<think>` boundaries.
- If you build the *thinking display* first without streaming, you're stuck regex-splitting a single completed string after the fact — solving the same problem worse, and you'll have to redo it once streaming lands anyway.

Build streaming first; thinking-display falls out of it.

## 3. Layers that change

This touches three layers. None of them are optional — skipping one leaves a broken link in the chain.

### 3.1 `modules/orchestration/inference.py` (LM Studio SDK usage)

`ModelInterface.invoke()` currently calls `self.model.respond(prompt, config={...})` and blocks for the full result. It needs to additionally pass an `on_prediction_fragment` callback (see the companion spec for exact mechanics). Each fragment callback fires synchronously as tokens arrive, tagged with a `reasoning_type`. Something needs to receive these fragments and push them onward to layer 3.2 — **this is the main open design decision, see section 5**.

The final `PredictionResult` (returned once `.respond()` unblocks) is still what gets persisted to `ChatLogStore` as before — streaming doesn't change what gets saved, only how the UI finds out about it as it's produced.

### 3.2 `modules/user_interface/host/app.py` (the JsApi/pywebview bridge)

This is the layer that needs the most conceptual change. `JsApi.send_chat()` today is a plain call-and-return method — JS calls it, awaits a promise, gets a dict back. `pywebview`'s `js_api` bridge is **one-directional on the way back**: Python can't spontaneously push a value into a pending JS promise mid-flight.

The way around this: pywebview's `Window` object (already stored via `get_main_window()` in `window_ref.py`) has an `evaluate_js(script: str)` method that runs arbitrary JS in the loaded page, callable at any time — including from inside the fragment callback while `send_chat` is still blocked and hasn't returned yet. So the shape becomes:

- `send_chat` starts the model call with a fragment callback.
- Each time the callback fires, it calls `get_main_window().evaluate_js(...)` with a small JS snippet that hands the fragment's data to a function the frontend defines (see 3.3).
- Once the model finishes, `send_chat` returns the final assembled dict exactly like today — this is still what resolves the original JS promise.

Net effect: the frontend gets a stream of "here's a piece" pushes *during* the call, then one final "here's the confirmed complete message" when the awaited call resolves.

### 3.3 `modules/user_interface/web/src/screens/chat.tsx` (frontend)

Two things need to exist here:

- A globally-reachable function pywebview's `evaluate_js` calls can invoke — e.g. registering `window.__onChatFragment = (fragment) => {...}` in a `useEffect` before calling `send_chat`. This is not the same mechanism as `pywebviewApi.ts`'s `getPywebviewApi()` — that's for JS-calls-Python. This is the reverse direction, so it's just a plain global function, not part of the typed `PywebviewApi` interface.
- State to accumulate fragments into a growing in-progress message bubble (distinct from the finalized list of persisted `ChatMessage`s), split by `reasoning_type` so the "thinking" portion and the "answer" portion can render differently (e.g. one collapsible/dimmed block, one normal). When the awaited `send_chat` call finally resolves, swap the in-progress accumulator out for the real persisted `ChatMessage`.

`stripThinking()` goes away entirely once this lands — there's no longer a single completed string to regex against; the split already happened fragment-by-fragment during streaming.

## 4. Data flow (end to end, one user message)

1. User submits a message in `chat.tsx`. It registers `window.__onChatFragment` (or ensures it's already registered) and calls `await api.send_chat(prompt)`.
2. `JsApi.send_chat` calls `ModelInterface.run()` → `_build_rag_prompt()` (unchanged) → `invoke()`.
3. `invoke()` calls `self.model.respond(prompt, config=..., on_prediction_fragment=<callback>)`.
4. Model starts generating. Each fragment triggers the callback synchronously, still inside the blocked `respond()` call.
5. The callback formats the fragment (content + reasoning_type) and calls `get_main_window().evaluate_js(...)`, pushing it into the page.
6. `chat.tsx`'s `window.__onChatFragment` receives each pushed fragment, appends to the in-progress bubble, splitting on `reasoning_type`.
7. Model finishes. `respond()` unblocks, returns a `PredictionResult`. `invoke()` builds and returns a `Message` as it does today.
8. `run()` persists it to `ChatLogStore` as today, `send_chat` returns the final dict.
9. `chat.tsx`'s `await api.send_chat(...)` resolves; finalize the message (replace in-progress accumulator with the confirmed message using the real `id`/`timestamp` from the backend).

## 5. Open design decisions — yours to make while implementing

- **Threading/safety of `evaluate_js` from a callback.** The fragment callback almost certainly fires from a background thread inside the `lmstudio` SDK (its websocket listener), not the Qt/pywebview main thread. pywebview's `evaluate_js` is generally documented as safe to call from any thread, but this hasn't been verified against this exact PySide6 setup — test it early, since if it's not safe you'd need to marshal the call onto the Qt main thread instead (there are pywebview/Qt patterns for this, but only worth solving if you actually hit a crash or a silent no-op).
- **Where to draw the "in-progress vs. persisted" line in `chat.tsx` state.** Simplest: a separate `streamingMessage` state slot rendered after the real `messages` list, cleared and replaced by a real entry once the call resolves.
- **What the collapsible thinking UI actually looks like.** A `<details>`/`<summary>` pair styled to match `chat.css`'s dark theme is the lowest-effort option; a custom expand/collapse component is more work for a nicer feel. Your call, no functional difference.
- **Error/cancellation handling mid-stream** (e.g. what if `run_desktop` was told to stop generating). Not currently handled anywhere in the codebase (no cancel button exists), so this is a "decide if you need it now or defer" call, not something existing code assumes either way.

## 6. Suggested build order

1. Get the fragment callback in `inference.py` working and just `print()`-ing fragments to confirm the SDK mechanics (companion spec walks through this in isolation).
2. Wire `evaluate_js` calls in `app.py`, confirm with a trivial JS snippet (e.g. `console.log`) that Python can push into the running page from inside the callback.
3. Add the `window.__onChatFragment` receiver in `chat.tsx`, confirm fragments show up (e.g. just log them) before building real UI around them.
4. Build the actual in-progress bubble + collapsible thinking section once the plumbing is confirmed end-to-end.

Confirming each hop independently before building the full UI will save time versus debugging all three layers at once if something's silently swallowed somewhere in the middle.
