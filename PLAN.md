# Reflection — MVP Plan

## What's Already Built

| Component | Status | Notes |
|---|---|---|
| Markdown parser | Done | Mistune AST → typed elements (headings, paragraphs, lists, code) |
| Chunker | Done | Structure-aware, token-budgeted, overlap carry, extracts `[[links]]` into metadata |
| ChromaDB store | Done | Upsert + query via `chroma_store.py` |
| VectorService | Done | Clean public API: `ingest_file`, `ingest_directory`, `query` |
| Embeddings | Done (OpenAI only) | `e_model.py` via `langchain-openai` — local option TBD |
| LMStudio inference | Done (basic) | `ModelInterface` in `inference.py`, raw prompt → LMStudio → response |
| Chat log (SQLite) | Done | `ChatLogStore`, messages persisted by id/timestamp |
| PyWebView host | Done | `JsApi` bridge wired: ingest, query, send_chat |
| React frontend | Unknown | Exists under `modules/user_interface/web/` — needs review |
| RAG loop | **Missing** | Vector search never called during chat — the core gap |
| File watcher | **Missing** | No automatic re-ingestion when notes change |
| `get_chats()` | **Stub** | JsApi method has no body — chat history not surfaced to UI |

---

## MVP Requirements

### 1. Chat window in PyWebView connected to LMStudio
- Review current React frontend state
- Ensure `send_chat` → `ModelInterface` → LMStudio path is functional end-to-end
- Implement `get_chats()` in `JsApi` to surface chat history to the UI

### 2. Parsing service — automatic + manual ingestion
- **File watcher**: monitor an Obsidian vault directory, debounce saves (only process after file idle for ~5 min)
- **Manual trigger**: UI can point at a specific file or folder to ingest on demand (already partially wired in `JsApi`)
- **File pinning**: user can reference a specific note to be used directly as context — bypasses vector search, injects full note text into prompt

### 3. Orchestration refactor
- **RAG mode**: user message → ChromaDB query → top-N chunks injected into prompt → LMStudio
- **Pin mode**: user selects a file → full text injected as context directly
- Keep `ModelInterface` thin — backend-agnostic so LMStudio → Ollama → Azure is a config swap
- No LangChain in the orchestration layer (already the case in `inference.py`, but `e_model.py` still uses `langchain-openai`)

### 4. Local embedding options
- Investigate: `sentence-transformers` (fully local, no API key), nomic-embed, LMStudio embedding endpoint
- Goal: remove `OPENAI_KEY` dependency from the ingestion pipeline
- `e_model.py` already has a `model_type` parameter designed for this — just needs a local backend added

### 5. Model selection
- Current: `qwen2.5-7b-instruct` via LMStudio
- Target content: educational, mathematical, scientific notes
- Candidates to evaluate: Qwen2.5-14B, DeepSeek-R1 (strong reasoning), Mistral-7B
- Decision deferred until RAG loop is working — model quality is irrelevant without context injection

### 6. Interface hygiene
- Module boundaries should be: `vectors/` owns ingestion and retrieval, `orchestration/` owns prompt assembly and LLM calls, `user_interface/` owns the bridge only
- No cross-module imports except through the service layer (`VectorService`, `ModelInterface`)

---

## Known Bugs / Debt

- `e_model.py` reads `OPENAI_KEY` from env but `.env` exports `OPENAI_API_KEY` — mismatch
- `orc_settings.py` default model is still `gpt-4o-mini` — leftover from pre-LMStudio
- `pipeline` class in `main_pipeline.py` has two `__init__` methods — Python silently ignores the first one
- `discord_presence.py` imports `click` but doesn't use it
- `get_chats()` in `JsApi` is an empty stub

---

## Environment

- OS: Nobara Linux (KDE)
- Python: 3.12 via uv venv
- Package manager: uv + pyproject.toml
- Local LLM: LMStudio (needs to be running before launching app)
- Entry point: `python reflection_app.py` (PyWebView + Vite dev server in parallel for dev mode)

---

## Open Questions

- What Obsidian vault path should the watcher monitor? (user config or hardcoded for MVP?)
- Does the React frontend have a working chat UI or does it need to be built?
- Local embeddings: sentence-transformers sufficient, or do we want embedding quality closer to OpenAI's?
