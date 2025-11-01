"""chunker.py – structure‑aware sliding‑window chunker

This module expects:
  * `elements`: a list of element dicts produced by the new MarkdownNoteParser
  * `doc_name`, `doc_path`: for provenance metadata

Each element dict **must** contain at least:
  - "type"  (e.g. heading, paragraph, list, code)
  - "text"  (flattened visible text)
  - Optionally for heading: "level"
  - Optionally for list: "items" (already joined into text by the parser)

`chunk_elements()` walks the element list once, building token‑bounded
chunks (≈800 tokens, 100‑token overlap) without slicing elements.
Every chunk dict carries:
    * text            – concatenated plain text of the chunk
    * tokens          – total token count (OpenAI tokenizer)
    * heading_path    – list of heading strings from H1..Hn providing context
    * element_types   – list of element.type values included in the chunk
    * metadata        – tags, links, chunk_idx, etc.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple
from itertools import islice
import hashlib
import re
import pandas as pd

import tiktoken

ENCODER_CACHE: Dict[str, Any] = {}

# ----------------------------- token utils ----------------------------------

def _get_encoder(model_name: str):
    if model_name not in ENCODER_CACHE:
        ENCODER_CACHE[model_name] = tiktoken.encoding_for_model(model_name)
    return ENCODER_CACHE[model_name]


def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
    enc = _get_encoder(model_name)
    return len(enc.encode(text))


# --------------------------- heading stack util -----------------------------

def _update_heading_path(path: List[str], level: int, title: str) -> List[str]:
    new_path = path[: level - 1] + [title]
    return new_path


# ------------------------------- chunker ------------------------------------

def _plain_text(elem: Dict[str, Any]) -> str:
    """Return a plaintext representation of an element for token counting."""
    if elem["type"] == "list":
        bullet = "- " if not elem.get("ordered") else "1. "
        return "\n".join(bullet + item for item in elem["items"])
    return elem.get("text", "")


def _collect_tags_links(elem_text: str) -> Tuple[List[str], List[str]]:
    links = re.findall(r"\[\[([^\]]+)\]\]", elem_text)
    tags = re.findall(r"(?<!\w)#(\w+)", elem_text)
    return tags, links


def chunk_elements(
    elements: List[Dict[str, Any]],
    doc_name: str,
    doc_path: str,
    *,
    max_tokens: int = 800,
    overlap: int = 100,
    model_name: str = "gpt-3.5-turbo",
) -> List[Dict[str, Any]]:
    """Return list of structure‑aware chunks built from element list."""

    chunks: List[Dict[str, Any]] = []
    heading_path: List[str] = []
    window: List[Dict[str, Any]] = []
    window_tokens = 0

    def emit(chunk_elems: List[Dict[str, Any]], chunk_idx: int):
        nonlocal chunks
        if not chunk_elems:
            return
        text = "\n".join(_plain_text(e) for e in chunk_elems).strip()
        tokens = count_tokens(text, model_name)
        # gather tags & links
        all_tags, all_links = set(), set()
        for e in chunk_elems:
            t, l = _collect_tags_links(_plain_text(e))
            all_tags.update(t)
            all_links.update(l)
        chunk_id = hashlib.md5(f"{doc_path}{chunk_idx}".encode()).hexdigest()[:10]
        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "tokens": tokens,
                "heading_path": heading_path.copy(),
                "element_types": [e["type"] for e in chunk_elems],
                "document_name": doc_name,
                "document_path": doc_path,
                "metadata": {
                    "tags": sorted(all_tags),
                    "links": sorted(all_links),
                    "chunk_index": chunk_idx,
                },
            }
        )

    chunk_idx = 0
    encoder = _get_encoder(model_name)

    for elem in elements:
        # update heading context
        if elem["type"] == "heading":
            if type(elem.get("level")) is not int:
                print(f"Warning: Element {elem} has no valid 'level' attribute, defaulting to 1.")
                elem["level"] = 1
            level = int(elem.get("level", 1))
            heading_path = _update_heading_path(heading_path, level, elem["text"])
        elem_text = _plain_text(elem)
        elem_tokens = len(encoder.encode(elem_text))
        # if adding this element will exceed window, emit current chunk
        if window_tokens + elem_tokens > max_tokens and window:
            emit(window, chunk_idx)
            chunk_idx += 1
            # compute overlap tail
            tail_tokens = 0
            tail: List[Dict[str, Any]] = []
            for e in reversed(window):
                t = len(encoder.encode(_plain_text(e)))
                tail_tokens += t
                tail.insert(0, e)
                if tail_tokens >= overlap:
                    break
            window = tail
            window_tokens = tail_tokens
        # add element
        window.append(elem)
        window_tokens += elem_tokens

    # flush last chunk
    if window:
        emit(window, chunk_idx)

    return chunks



class MarkdownChunker:
    """
    Chunker for Markdown elements produced by MarkdownNoteParser.
    - This chunker is meant to take in a list of elements (from ast) and then combine them into usable chunks.
    - Chunk sizes can vary based on the number of tokens. A token limit will be set.
    - Text fields in the output chunks should be plain text but representative of the original Markdown structure.
    - Lists extracted from the Items field of the AST should be recognizable as a list, such is the same for headings.
    - Links, Tags, and other metadata should be preserved in the output chunks.
    - Abstraction of each extraction method should be practiced. (e.g. _format_links, _format_tags, _format_headings, _format_lists, etc.)
    - And example of the AST Elements based data frame or list can be found in the output of the test_one.py file.


    """

    chunk_size: int
    overlap: int
    elements: List[Dict[str, Any]]
    df_output: pd.DataFrame
    df_ephem: pd.DataFrame


    def __init__(self, chunk_size: int = 800, overlap: int = 100, elements = List[Dict[str, Any]]):
        """
        Initialize the MarkdownChunker with chunk size and overlap.
        :param chunk_size: Maximum number of tokens per chunk.
        :param overlap: Number of tokens to overlap between chunks.
        :param elements: List of elements to be chunked.
        """
        self.chunk_size = chunk_size
        self.overlap    = overlap
        self.elements   = elements

    def _chunk_normalize(self) -> pd.DataFrame:
        """
        Chunk markdown elements passed into the class in a normalized fashion. 
        This means:
        - No fomratting is applied in final chunks.
        - Possible removal of markdown syntax and typical line breaks.
        - Focus is placed more on textual extraction rather than formatting semantics and structure.

        NOTE: W.I.P Feature is not yet implemented.
        """
        return pd.DataFrame(self.elements)
    
    def _chunk_to_structured(self) -> pd.DataFrame:
        """
        Chunk markdown elements passed into the class in a structured fashion.
        This means:
        - Formatting is applied to the final chunks.
        - Markdown syntax and typical line breaks are preserved.
        - Focus is placed on maintaining the original structure and semantics of the markdown content.
        Required methods/techniques:
        - When chunkin, ensure flow, order, and structure are retained and that paragraphs are chronologically ordered.
        - Detect and format all elements not just text, this will allow LLM to understand sections.
        - Include key metadata points in addition to chunked text such as section headings, includesList, includesTags, and includesLinks.
        NOTE: W.I.P Feature is not yet implemented.
        """
    
    def _format_lists(self, items):
        """
        Format list elements into a readable string format, identifying it as ordered or undordered visibly. 
        """        
    def _format_headings(self, elems):
        """
        Format heading elements into a structured format, preserving the hierarchy and level of each heading.
        """

    def _format_links(self, elems):
        """
        Format link elements into a structured format, preserving the link text and URL.
        """
    
    def _formate_tags(self, elems):
        """
        Format tag elements into a structured format, preserving the tag text.
        """