from pprint import pprint

def dump_ast(nodes, depth=0):
    """Pretty-print Mistune AST structure (types, keys, brief values)."""
    indent = "  " * depth
    if isinstance(nodes, list):
        for n in nodes:
            dump_ast(n, depth)
        return
    if not isinstance(nodes, dict):
        print(f"{indent}- <non-dict node>:", repr(nodes))
        return

    node_type = nodes.get("type")
    keys = [k for k in nodes.keys()]
    print(f"{indent}• type={node_type} keys={keys}")
    # Show short preview for common fields
    if "level" in nodes:
        print(f"{indent}  level={nodes['level']}")
    if "raw" in nodes:
        print(f"{indent}  raw={nodes['raw'][:60]!r}")
    if "text" in nodes:
        print(f"{indent}  text={nodes['text'][:60]!r}")
    if "ordered" in nodes:
        print(f"{indent}  ordered={nodes['ordered']}")

    # Recurse into children if present
    children = nodes.get("children")
    if isinstance(children, list):
        for child in children:
            dump_ast(child, depth + 1)
