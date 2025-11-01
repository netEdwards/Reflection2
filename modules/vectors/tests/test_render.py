from mistune import Markdown
import pytest
from sympy import im

from modules.vectors.components.parser import MarkdownNoteParser


@pytest.mark.parser
def test_parser_init(tmp_path):
    md_text = """# Heading 1

Some paragraph text with **bold** and *italic*.

- Item 1
- Item 2
"""
    p = tmp_path / "sample.md"
    p.write_text(md_text)
    
    parser = MarkdownNoteParser()
    nodes = parser.parse_markdown_file(p)
    
    print("\n=== PARSED AST ===")
    from pprint import pprint
    pprint(nodes, width=100)
    