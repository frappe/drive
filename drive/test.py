import base64
import pycrdt
import frappe


def walk(node, depth=0):
    indent = "  " * depth

    if isinstance(node, pycrdt.XmlText):
        print(f"{indent}Text: {str(node)}")
        return

    if isinstance(node, pycrdt.XmlElement):
        attrs = dict(node.attributes)
        print(f"{indent}Element: {attrs}")
        for child in list(node.children):
            walk(child, depth + 1)

    elif isinstance(node, pycrdt.XmlFragment):
        print(f"{indent}Fragment:")
        for child in list(node.children):
            walk(child, depth + 1)


def execute():
    b64_data = frappe.db.get_value("Drive Document", "uu9aak6l3p", "content")
    update_bytes = base64.b64decode(b64_data)

    doc = pycrdt.Doc()
    doc.apply_update(update_bytes)
    frag = doc.get("default", type=pycrdt.XmlFragment)
    frag2 = doc.get("content", type=pycrdt.XmlFragment)
    print(list(frag2.children))
    # walk(frag)
