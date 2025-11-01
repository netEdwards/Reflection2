import re
from pathlib import Path
import mistune
from modules.vectors.utils.file_utils import read_file
from typing import List, Dict, Any


class MarkdownNoteParser:
    def __init__(self):
        # Mistune AST renderer for markdown
        self.md_parser = mistune.create_markdown(renderer="ast")

    def parse_markdown_file(self, path: Path) -> List[Dict[str, Any]]:
        """
        Parse the markdown file at 'path' into nodes. 
        Params:
        - path: Path to the markdown file.
        Returns:
        - nodes: List of parsed nodes (dicts).
        """
        raw_text = read_file(path)
        nodes = self.md_parser(raw_text)
        
    def _to_elements(self, nodes) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        
        def walk(n):
                if isinstance(node, list):
                    for n in node: walk(n); return
                if not isinstance(node)


