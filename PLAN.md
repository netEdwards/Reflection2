# Reflection — MVP Plan

## What's Already Built

| Component | Status | Notes |
|---|---|---|
| Markdown parser | Done | Mistune AST → typed elements (headings, paragraphs, lists, code) |
| Chunker | Done | Structure-aware, token-budgeted, overlap carry, extracts `[[links]]` into metadata |
| ChromaDB store | Done | Upsert + query via `chroma_store.py` |
| VectorService | Done | Clean public API: `ingest_file`, `ingest_directory`, `query` |
| Embeddings | Done (local) | `e_model.py` via `lmstudio` SDK, `text-embedding-nomic-embed-text-v1.5` — OpenAI dependency removed |
| LMStudio inference | Done | `ModelInterface` in `inference.py`, includes RAG prompt injection |
| RAG loop | Done | `ModelInterface._build_rag_prompt()` queries `VectorService` and folds top-5 chunks into the prompt |
| Chat log (SQLite) | Done | `ChatLogStore`, messages persisted by id/timestamp, `list_messages()` added for history |
| PyWebView host | Done | `JsApi` bridge wired: ingest, query, send_chat, get_chats |
| React frontend | Done (basic) | Home, DataViewer, QueryScreen, and a Chat screen (`chat.tsx`) wired to `send_chat`/`get_chats`. Chat now streams responses token-by-token with a live thinking/answer split. Window launches maximized; shared `Header` component across screens; Home nav reordered (Chat first); app shell is a flex row so a threads sidebar can be added later without restructuring. |
| File watcher | **Missing** | No automatic re-ingestion when notes change |
| Chat threads/history UI | **Missing** | Messages persist to SQLite but there's no thread concept yet — single flat log |
| Knowledge-graph-aware retrieval | **Missing** | `[[links]]` extracted into chunk metadata but never used at query time — see Open Questions |

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

- `pipeline` class in `main_pipeline.py` has two `__init__` methods — Python silently ignores the first one
- `discord_presence.py` imports `click` but doesn't use it
- `_LINK_RE` in `chunker.py` (`\[\[([^\]]+)\]\]`) matches Obsidian's embed syntax `![[...]]` too (the `!` doesn't break the match), so embedded images/attachments get swept into chunk `metadata["links"]` as if they were note-to-note links. Confirmed happening in the real vault (7 files use `![[...]]`). Needs a negative lookbehind or equivalent to exclude the `!`-prefixed form.
- `langchain-openai` dependency in `pyproject.toml` is now dead weight — embeddings no longer use it
- Pre-existing unused-var TS errors in `dataviewer.tsx`/`queryscreen.tsx` that would fail `tsc -b`/`npm run build` (dev mode via vite is unaffected)

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
- Chat threads: traditional per-conversation threads like most chatbot apps, or something else? Undecided — SQL storage exists (`ChatLogStore`) but nothing above it treats messages as belonging to separate conversations yet.
- Link resolution: wikilink targets (`[[Note Name]]`) aren't resolved to actual file paths — same note title can exist in multiple folders (e.g. two different "Statistics" notes, one in /statistics one in /biology). Decided to defer a real resolver until there's architectural pressure to build one; in the meantime, lean on Chroma's `where` filter against filename at query time to close part of the gap.
- Planning/tracking: currently just this file. Once there are too many moving parts to track here, plan to move task tracking to GitHub (issues/project board) instead of continuing to expand this doc.

---

## Near-term backlog (added 2026-07-04)

- Fix `_LINK_RE` to exclude embed syntax `![[...]]` (see Known Bugs above)
- Chat threads/history: SQLite storage exists but nothing above it groups messages into conversations yet — needs the traditional-vs-alternative decision above resolved first. The app shell (`.app-container`) is now a flex row specifically so a threads sidebar can be added later without restructuring existing screens.
