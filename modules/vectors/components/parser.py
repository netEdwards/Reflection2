# parser.py — Mistune AST → flat elements
from pathlib import Path
from typing import List, Dict, Any
import mistune

def _extract_text(node) -> str:
    # Flatten inline content (strong/emphasis/link/code_inline, etc.)
    if isinstance(node, list):
        return "".join(_extract_text(ch) for ch in node)
    if not isinstance(node, dict):
        return ""
    t = node.get("type")
    if t == "text":
        return node.get("raw") or node.get("text") or ""
    # recurse into children for other inline types
    return _extract_text(node.get("children", []))

def _to_elements(ast) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    def walk(n):
        if isinstance(n, list):
            for c in n:
                walk(c)
            return
        if not isinstance(n, dict):
            return

        t = n.get("type")
        
        # heading is in {'attrs': {'level': 1}}
        
            
        if t == "heading":
            txt = _extract_text(n.get("children", []))
            level = int(n.get("attrs", {}).get("level", 1))
            print(f"Current heading level: {level}")
            out.append({"type": "heading", "text": txt.strip(), "level": level})

        elif t in ("paragraph", "block_quote"):
            txt = _extract_text(n.get("children", []))
            if txt.strip():
                out.append({"type": "paragraph", "text": txt.strip()})

        elif t == "list":
            ordered = bool(n.get("ordered", False))
            items = []
            for li in n.get("children", []):
                items.append(_extract_text(li.get("children", [])).strip())
            out.append({"type": "list", "items": items, "ordered": ordered})

        elif t == "block_code":
            code = n.get("text") or n.get("raw") or ""
            out.append({"type": "code", "text": code})

        # Walk through any container nodes we didn’t explicitly capture
        for c in n.get("children", []) or []:
            walk(c)

    walk(ast)
    return out

class MarkdownNoteParser:
    def __init__(self):
        self._md = mistune.create_markdown(renderer="ast")

    def parse_markdown_file(self, path: Path) -> List[Dict[str, Any]]:
        raw = Path(path).read_text(encoding="utf-8")
        ast = self._md(raw)
        return _to_elements(ast)
