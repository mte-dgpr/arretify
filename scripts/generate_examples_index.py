#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from dataclasses import dataclass
from pathlib import Path
from typing import List

CURRENT_DIR = Path(__file__).parent.resolve()
EXAMPLES_DIR = (CURRENT_DIR / ".." / "examples").resolve()
OUTPUT_FILE = EXAMPLES_DIR / "index.html"
TEMPLATE_FILE = CURRENT_DIR / "generate_examples_index.tmpl.html"
PDF_DIR = EXAMPLES_DIR / "arretes_pdf"
HTML_DIR = EXAMPLES_DIR / "arretes_html"


@dataclass
class TreeNode:
    path: Path
    children: List["TreeNode"] | None = None
    """None if leaf node (file), list of TreeNode if directory"""


def build_tree(root: Path) -> TreeNode:
    """
    Recursively builds a TreeNode structure from the given root directory.
    Leaf nodes are files, non-leaf nodes are directories with children.
    Only .pdf and .html files are included as leaves.
    """
    if root.is_file():
        return TreeNode(path=root, children=None)
    elif root.is_dir():
        return TreeNode(path=root, children=[build_tree(entry) for entry in sorted(root.iterdir())])
    else:
        raise ValueError(f"Path {root} is neither a file nor a directory")


def render_tree(node: TreeNode, base_path: Path) -> str:
    """
    Renders the TreeNode structure as an HTML unordered list.
    Directories are rendered as nested lists, files as list items with links.
    """
    # File node
    if node.children is None:
        # Only .pdf files are allowed as leaves
        ext = node.path.suffix
        base = node.path.stem
        if ext != ".pdf":
            raise ValueError(f"Unexpected file type: {node.path}")
        rel_path = node.path.relative_to(PDF_DIR).parent
        html_file_path = HTML_DIR / rel_path / f"{base}.html"
        pdf_file_path = PDF_DIR / rel_path / f"{base}.pdf"
        if not html_file_path.exists():
            raise FileNotFoundError(f"Missing HTML file for: {node.path} -> {html_file_path}")
        if not pdf_file_path.exists():
            raise FileNotFoundError(f"Missing PDF file for: {node.path} -> {pdf_file_path}")
        html_url = html_file_path.relative_to(HTML_DIR.parent).as_posix()
        pdf_url = pdf_file_path.relative_to(PDF_DIR.parent).as_posix()
        return f'<li class="file"><span class="file-name">{base}</span><span class="spacer"></span> <span class="file-urls"><a href="{pdf_url}">pdf</a> | <a href="{html_url}">html</a></span></li>'  # noqa: E501

    # Directory node
    else:
        dir_name = node.path.relative_to(base_path).as_posix()
        if dir_name == ".":
            return "".join(render_tree(child, node.path) for child in node.children)

        html = f'<li class="dir">{dir_name}<ul>'
        for child in node.children:
            html += render_tree(child, node.path)
        html += "</ul></li>"
        return html


def main():
    tree = build_tree(PDF_DIR)
    tree_html = "<ul>" + render_tree(tree, PDF_DIR) + "</ul>"
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as tmpl:
        template = tmpl.read()
    html_content = template.replace("{{examples_tree}}", tree_html)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Index generated at {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
