from pathlib import Path

import markdown

CSS = """
body { font-family: sans-serif; line-height: 1.5; margin: 2em; }
code, pre { background: #f0f0f0; padding: 0.2em 0.4em; }
pre { padding: 1em; overflow-x: auto; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 1em; color: #555; }
img { max-width: 100%; }
"""


def markdown_to_html(markdown_text: str) -> str:
    # Raw HTML is deregistered rather than left to pass through: an
    # untrusted .md file could otherwise embed e.g. <meta http-equiv="refresh">
    # to open the system browser with no click, or <img>/<form> tags to
    # reach the network outside the markdown-image path.
    converter = markdown.Markdown()
    converter.preprocessors.deregister("html_block")
    converter.inlinePatterns.deregister("html")
    body = converter.convert(markdown_text)
    return f"<html><head><style>{CSS}</style></head><body>{body}</body></html>"


def render_file(path: Path) -> str:
    # utf-8-sig also accepts plain UTF-8 (no BOM); it only strips a BOM
    # when one is present, so both are read the same way.
    text = path.read_text(encoding="utf-8-sig")
    return markdown_to_html(text)
