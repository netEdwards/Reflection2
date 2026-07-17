# Reflection

An off-grid personal knowledge system — chat with your Obsidian notes via a local LLM. Point it at a vault, it parses and embeds your notes, and you can talk to a locally-running model that answers using your own material as context. No cloud calls, no accounts, everything runs on your machine.

This is a solo side project, under active development, not a polished product.

## Status

Working right now:
- Markdown parsing/chunking of an Obsidian vault, embedded into a local ChromaDB store
- Retrieval-augmented chat backed by a local model via LM Studio (no OpenAI/cloud dependency)
- A desktop app (PyWebView + React) with a chat screen, a manual ingestion screen, and a raw query screen
- Streaming responses, with the model's reasoning shown separately from its answer as it generates
- Chat history persisted locally in SQLite

In progress:
- Threaded/multi-conversation chat — the backend (storage + API) supports separate conversation threads now; the frontend hasn't been wired up to it yet, so the UI still behaves like one continuous chat for the moment.

Not started yet: automatic re-ingestion when notes change, and a few retrieval improvements (see below).

## Getting started

Prerequisites:
- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- Node.js/npm
- [LM Studio](https://lmstudio.ai/), running locally with a chat model and an embedding model downloaded (currently developed against a small Qwen3 model and Nomic's embedding model — any locally-servable chat + embedding model pair should work with minor config)

Setup:

```bash
# Python deps
uv sync

# Frontend deps
cd modules/user_interface/web
npm install
```

Running it (two terminals):

```bash
# Terminal 1 — frontend dev server
cd modules/user_interface/web
npm run dev

# Terminal 2 — the app itself (make sure LM Studio's local server is running first)
uv run reflection_app.py
```

## Design direction

- **Desktop, not web** — PyWebView (PySide6/Qt) hosting a React + TypeScript frontend, not a browser-hosted app.
- **Local-first** — inference and embeddings both run through LM Studio; nothing leaves the machine.
- **RAG over your own notes** — notes are chunked, embedded, and retrieved by similarity at chat time; the orchestration layer is kept thin and model-agnostic rather than built around any particular backend.
- **SQLite for state** — chat history (and, increasingly, conversation structure) is just a local SQLite file, no external database.

## Ideas floating around (not commitments)

Loosely ordered by how likely they are to actually happen soon:
- Finishing the threaded-conversation UI
- Watching the vault directory and re-ingesting notes automatically instead of manual triggers
- Using the note-to-note links already extracted during chunking to inform retrieval, not just plain similarity search

## Contributing

This is a personal project and I'm not set up to review outside code contributions right now — I don't have the bandwidth to properly review PRs.

That said, if you run into a bug or have an idea, opening an issue (or joining the discussion on an existing one) is genuinely welcome and appreciated — that kind of feedback helps regardless of whether code ever gets merged.

Pull requests against open issues won't be accepted unless you've been invited as a contributor. If you'd like to contribute and are up for reaching out first, email me at aedwards0603@gmail.com or find me on Discord as `apetoot52` — happy to talk about it.
