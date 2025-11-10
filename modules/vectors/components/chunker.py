# chunker.py — structure-aware sliding window chunker
from __future__ import annotations
from typing import List, Dict, Any, Tuple
from pathlib import Path
import hashlib
import re
import tiktoken

# Use the same tokenizer family as OpenAI embeddings (cl100k_base)
# so your "800 tokens" is the same 800 the embedder sees.
_ENC = tiktoken.get_encoding("cl100k_base")

def _count_tokens(text: str) -> int:
    return len(_ENC.encode(text))

def _update_heading_path(path: List[str], level: int, title: str) -> List[str]:
    # Keep H1..Hlevel; replace current level with new title
    new_path = (path[: max(level - 1, 0)]) + [title]
    return new_path

def _format_elem(e: Dict[str, Any]) -> str:
    t = e["type"]
    if t == "heading":
        # Render minimal markdown so reconstruction “feels” right to a reader
        level = int(e.get("level", 1))
        return f"{'#' * max(level,1)} {e.get('text','').strip()}"
    if t == "list":
        bullet = ("1. " if e.get("ordered") else "- ")
        return "\n".join(bullet + item for item in e.get("items", []))
    if t == "code":
        return f"```\n{e.get('text','')}\n```"
    # paragraph / quote
    return e.get("text", "")

_TAG_RE   = re.compile(r"(?<!\w)#(\w+)")
_LINK_RE  = re.compile(r"\[\[([^\]]+)\]\]")

def _tags_links_from_text(text: str) -> Tuple[List[str], List[str]]:
    return list(set(_TAG_RE.findall(text))), list(set(_LINK_RE.findall(text)))

def chunk_elements(
    elements: List[Dict[str, Any]],
    *,
    doc_name: str,
    doc_path: str,
    max_tokens: int = 800,
    overlap: int = 100,
) -> List[Dict[str, Any]]:
    """
    Build chunks that:
      - never cut through an element
      - track a live heading_path (H1..Hn) for context
      - preserve basic markdown formatting for readability
      - maintain a token budget with an overlap “tail”
    """
    chunks: List[Dict[str, Any]] = []
    heading_path: List[str] = []

    window: List[Dict[str, Any]] = []
    window_tokens = 0
    chunk_idx = 0

    def emit(chunk_elems: List[Dict[str, Any]], idx: int):
        if not chunk_elems:
            return
        # Join with double newlines to mimic paragraph breaks
        text = "\n\n".join(_format_elem(e) for e in chunk_elems).strip()
        tokens = _count_tokens(text)
        tags, links = _tags_links_from_text(text)

        # deterministic id from path + index
        digest = hashlib.md5(f"{doc_path}:{idx}".encode("utf-8")).hexdigest()[:12]

        chunks.append({
            "chunk_id": digest,
            "text": text,
            "tokens": tokens,
            "heading_path": heading_path.copy(),
            "element_types": [e["type"] for e in chunk_elems],
            "document_name": doc_name,
            "document_path": doc_path,
            "metadata": {
                "chunk_index": idx,
                "tags": sorted(tags),
                "links": sorted(links),
            },
        })

    for e in elements:
        if e["type"] == "heading":
            lvl = int(e.get("level", 1))
            heading_path = _update_heading_path(heading_path, lvl, e.get("text","").strip())

        etext = _format_elem(e)
        etoks = _count_tokens(etext)

        # If this element would overflow, emit current window and carry an overlap tail
        if window and window_tokens + etoks > max_tokens:
            emit(window, chunk_idx)
            chunk_idx += 1

            # Build overlap tail in element units (no mid-element slicing)
            tail: List[Dict[str, Any]] = []
            tail_tokens = 0
            for prev in reversed(window):
                ptxt = _format_elem(prev)
                ptok = _count_tokens(ptxt)
                tail.insert(0, prev)
                tail_tokens += ptok
                if tail_tokens >= overlap:
                    break

            window = tail
            window_tokens = tail_tokens

        window.append(e)
        window_tokens += etoks

    if window:
        emit(window, chunk_idx)

    return chunks
