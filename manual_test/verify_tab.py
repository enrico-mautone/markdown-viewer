import sys
import tkinter as tk
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from markdownviewer.tab import MarkdownTab

opened_urls = []
webbrowser.open = lambda url: opened_urls.append(url)

HERE = Path(__file__).resolve().parent

clicked_urls = []


def run_case(name, file_path, expected_snippets):
    root = tk.Tk()
    tab = MarkdownTab(root, file_path)
    tab.pack(fill="both", expand=True)
    root.update()

    text = tab.get_page_text()
    print(f"[{name}] page text: {text!r}")
    for snippet in expected_snippets:
        assert snippet in text, f"[{name}] expected {snippet!r} in page text"

    if name == "ok":
        tab._handle_link_click("https://example.com")
        assert opened_urls == ["https://example.com"], opened_urls
        print(f"[{name}] link click opened via webbrowser.open: {opened_urls}")

    root.destroy()


run_case("ok", HERE / "sample-ok.md", ["Sample", "bold", "italic", "plain code block"])
def run_image_case():
    root = tk.Tk()
    tab = MarkdownTab(root, HERE / "sample-image.md")
    tab.pack(fill="both", expand=True)
    root.update()
    images = tab.image_names()
    print(f"[image] loaded images: {images}")
    # image_names() always includes Tk's built-in icons (::tk::icons::*) and
    # a 0x0 placeholder tkinterweb creates before the real fetch resolves, so
    # neither presence nor count proves the relative image actually loaded.
    # Only a real fetch produces a nonzero-width image under this name prefix.
    fetched = [n for n in images if n.startswith("_tkinterweb_img_")]
    assert fetched, f"expected a fetched image, got {images}"
    widths = [root.tk.call("image", "width", n) for n in fetched]
    assert any(w > 0 for w in widths), f"relative image never resolved (widths: {widths})"
    print(f"[image] fetched image widths: {widths}")
    root.destroy()


run_case("image-text", HERE / "sample-image.md", ["With image"])
run_image_case()
run_case("missing", HERE / "does-not-exist.md", ["Impossibile aprire il file", "File non trovato"])

print("ALL CASES RAN WITHOUT CRASHING")
