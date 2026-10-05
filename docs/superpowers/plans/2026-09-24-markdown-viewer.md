# Markdown Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task, using checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Build a Python desktop app that opens and renders Markdown files
in read-only tabs — no editing or saving anywhere.

**Architecture:** `render.py` holds pure functions (file read + markdown→HTML
conversion) with no Tk dependency, so it's unit-testable. `tab.py` wraps a
`tkinterweb.HtmlFrame` per open file (GUI, manually tested). `app.py` is the
entry point: main window, File menu, `ttk.Notebook` of tabs.

**Tech Stack:** Python 3, `tkinter` (stdlib), `tkinterweb`, `markdown`, `pytest`
for the `render.py` unit tests.

**Spec:** `projects/markdownviewer/docs/design-markdown-viewer.md`

## Global Constraints

- No file-writing capability anywhere in the app (spec: "Esplicitamente fuori
  scope").
- Only markdown "base" features: headings, lists, bold/italic, links,
  images, code blocks without syntax highlighting (spec table).
- Only dialog-based file opening (Ctrl+O / File menu), no drag&drop, no CLI
  args (spec table).
- Files open in tabs (`ttk.Notebook`), one tab per file (spec table).
- Automated tests only for `render.py` logic; GUI is manually verified
  (spec "Testing" section).

## Review Focus

- Opening the same file twice must focus the existing tab, not duplicate it
  (spec "File già aperto") — covered in Task 4's manual verification step.
- A missing/unreadable/non-UTF-8 file must show an in-tab error message and
  leave the rest of the app usable, not crash (spec "Errori") — covered in
  Task 2's tests and Task 3's error-path wiring.
- Clicking an external link must open the system browser, not navigate
  inside the app (spec "Link esterni") — covered in Task 3's manual
  verification step.
- Relative image paths must resolve against the markdown file's own folder,
  not the app's working directory (spec "Rendering") — covered in Task 3.
- Malformed markdown must render best-effort, not raise (spec "Errori") —
  covered in Task 2's tests (the `markdown` library is tolerant by
  construction; test asserts no exception on garbled input).

---

### Task 1: Project scaffolding

**Files:**
- Create: `projects/markdownviewer/requirements.txt`
- Create: `projects/markdownviewer/requirements-dev.txt`
- Create: `projects/markdownviewer/markdownviewer/__init__.py`
- Create: `projects/markdownviewer/tests/__init__.py`

**Interfaces:**
- Produces: an installable `markdownviewer` package directory that later
  tasks add modules to.

- [ ] **Step 1: Create the package and test directories with empty inits**

```python
# projects/markdownviewer/markdownviewer/__init__.py
```

```python
# projects/markdownviewer/tests/__init__.py
```

- [ ] **Step 2: Write requirements files**

```text
# projects/markdownviewer/requirements.txt
tkinterweb>=3.24
markdown>=3.6
```

```text
# projects/markdownviewer/requirements-dev.txt
-r requirements.txt
pytest>=8.0
```

- [ ] **Step 3: Install dependencies**

Run: `pip install -r projects/markdownviewer/requirements-dev.txt`
Expected: `tkinterweb`, `markdown`, `pytest` install without errors.

- [ ] **Step 4: Commit**

```bash
git add projects/markdownviewer/requirements.txt projects/markdownviewer/requirements-dev.txt projects/markdownviewer/markdownviewer/__init__.py projects/markdownviewer/tests/__init__.py
git commit -m "chore: scaffold markdownviewer package"
```

---

### Task 2: `render.py` — markdown-to-HTML conversion (TDD)

**Files:**
- Create: `projects/markdownviewer/markdownviewer/render.py`
- Test: `projects/markdownviewer/tests/test_render.py`

**Interfaces:**
- Produces:
  - `markdown_to_html(markdown_text: str) -> str` — wraps the converted
    body in a minimal HTML document with an embedded `<style>` block.
  - `render_file(path: pathlib.Path) -> str` — reads `path` as UTF-8 text
    and returns `markdown_to_html(text)`. Raises `FileNotFoundError` if the
    file doesn't exist, `UnicodeDecodeError` if it isn't valid UTF-8 —
    these propagate unchanged for the caller (Task 3) to catch.
- Consumes: nothing (pure stdlib + `markdown` package).

- [ ] **Step 1: Write failing tests**

```python
# projects/markdownviewer/tests/test_render.py
import pytest
from markdownviewer.render import markdown_to_html, render_file


def test_markdown_to_html_converts_heading():
    html = markdown_to_html("# Title")
    assert "<h1>Title</h1>" in html


def test_markdown_to_html_wraps_in_style_block():
    html = markdown_to_html("body text")
    assert "<style>" in html
    assert "</style>" in html


def test_markdown_to_html_handles_garbled_input_without_raising():
    html = markdown_to_html("# Unclosed *bold\n\n[bad link](")
    assert isinstance(html, str)


def test_render_file_reads_and_converts(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("# Hello\n\nSome **bold** text.", encoding="utf-8")

    html = render_file(md_file)

    assert "<h1>Hello</h1>" in html
    assert "<strong>bold</strong>" in html


def test_render_file_missing_file_raises(tmp_path):
    missing = tmp_path / "does-not-exist.md"

    with pytest.raises(FileNotFoundError):
        render_file(missing)


def test_render_file_bad_encoding_raises(tmp_path):
    bad_file = tmp_path / "bad-encoding.md"
    bad_file.write_bytes(b"\xff\xfe# not valid utf-8 \xff")

    with pytest.raises(UnicodeDecodeError):
        render_file(bad_file)
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `pytest projects/markdownviewer/tests/test_render.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'markdownviewer.render'`

- [ ] **Step 3: Write minimal implementation**

```python
# projects/markdownviewer/markdownviewer/render.py
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
    body = markdown.markdown(markdown_text)
    return f"<html><head><style>{CSS}</style></head><body>{body}</body></html>"


def render_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return markdown_to_html(text)
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `pytest projects/markdownviewer/tests/test_render.py -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add projects/markdownviewer/markdownviewer/render.py projects/markdownviewer/tests/test_render.py
git commit -m "feat: markdown-to-html rendering with tests"
```

---

### Task 3: `tab.py` — single-file viewer tab (GUI, manual verification)

**Files:**
- Create: `projects/markdownviewer/markdownviewer/tab.py`

**Interfaces:**
- Consumes: `render_file(path: Path) -> str` from Task 2.
- Produces: `MarkdownTab(parent: tk.Widget, file_path: Path)` — a
  `tkinterweb.HtmlFrame` subclass instance with attribute `.file_path`
  (the `Path` it was built from), used by Task 4 to detect already-open
  files and set tab titles.

- [ ] **Step 1: Implement the tab widget**

```python
# projects/markdownviewer/markdownviewer/tab.py
import webbrowser
from pathlib import Path

from tkinterweb import HtmlFrame

from markdownviewer.render import render_file

ERROR_TEMPLATE = """
<html><body style="font-family: sans-serif; color: #a00;">
<h2>Impossibile aprire il file</h2>
<p>{message}</p>
</body></html>
"""


class MarkdownTab(HtmlFrame):
    def __init__(self, parent, file_path: Path):
        super().__init__(parent, messages_enabled=False)
        self.file_path = file_path
        self.on_link_click(self._handle_link_click)
        self._load()

    def _load(self):
        try:
            html = render_file(self.file_path)
        except FileNotFoundError:
            html = ERROR_TEMPLATE.format(message=f"File non trovato: {self.file_path}")
        except UnicodeDecodeError:
            html = ERROR_TEMPLATE.format(
                message=f"Il file non è testo UTF-8 valido: {self.file_path}"
            )
        except OSError as exc:
            html = ERROR_TEMPLATE.format(message=f"Errore di lettura: {exc}")

        self.load_html(html, base_url=str(self.file_path.parent) + "/")

    def _handle_link_click(self, url: str):
        if url.startswith("http://") or url.startswith("https://"):
            webbrowser.open(url)
```

- [ ] **Step 2: Manual verification**

Create three sample files and confirm each renders and behaves correctly
before moving on (no automated GUI test — per spec, GUI is manually
verified):

```markdown
<!-- sample-ok.md -->
# Sample

Some **bold** and *italic* text, a [link](https://example.com), and:

```code
plain code block
```
```

```markdown
<!-- sample-image.md -->
# With image

![alt text](./image.png)
```

(place any small `.png` next to `sample-image.md` as `image.png`)

Steps:
1. Instantiate a `tk.Tk()` root, add a `MarkdownTab(root, Path("sample-ok.md"))`, `pack(fill="both", expand=True)`, `root.mainloop()`.
2. Confirm heading, bold, italic, link, and code block render.
3. Click the link — confirm it opens in the system's default browser, not inside the Tk window.
4. Repeat with `sample-image.md` — confirm the image displays (relative path resolved).
5. Repeat with a path to a file that doesn't exist — confirm the red error message appears instead of a crash.

- [ ] **Step 3: Commit**

```bash
git add projects/markdownviewer/markdownviewer/tab.py
git commit -m "feat: read-only markdown tab widget"
```

---

### Task 4: `app.py` — main window, File menu, tabs

**Files:**
- Create: `projects/markdownviewer/markdownviewer/app.py`
- Create: `projects/markdownviewer/markdownviewer/__main__.py`

**Interfaces:**
- Consumes: `MarkdownTab(parent, file_path)` from Task 3.
- Produces: `main()` — starts the app; used by `__main__.py`.

- [ ] **Step 1: Implement the main window**

```python
# projects/markdownviewer/markdownviewer/app.py
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from markdownviewer.tab import MarkdownTab


class MarkdownViewerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Markdown Viewer")
        self.root.geometry("900x700")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self._open_paths: dict[Path, str] = {}  # resolved path -> notebook tab id

        self._build_menu()
        self.root.bind("<Control-o>", lambda _event: self.open_files())
        self.root.bind("<Control-w>", lambda _event: self.close_current_tab())

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Apri file...", accelerator="Ctrl+O", command=self.open_files)
        file_menu.add_command(label="Chiudi tab", accelerator="Ctrl+W", command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def open_files(self):
        paths = filedialog.askopenfilenames(
            title="Apri file Markdown",
            filetypes=[("Markdown", "*.md *.markdown"), ("Tutti i file", "*.*")],
        )
        for raw_path in paths:
            self._open_one(Path(raw_path).resolve())

    def _open_one(self, path: Path):
        if path in self._open_paths:
            self.notebook.select(self._open_paths[path])
            return

        tab = MarkdownTab(self.notebook, path)
        self.notebook.add(tab, text=path.name)
        tab_id = str(tab)
        self._open_paths[path] = tab_id
        self.notebook.select(tab)

    def close_current_tab(self):
        selected = self.notebook.select()
        if not selected:
            return
        self.notebook.forget(selected)
        self._open_paths = {p: tid for p, tid in self._open_paths.items() if tid != selected}


def main():
    root = tk.Tk()
    MarkdownViewerApp(root)
    root.mainloop()
```

```python
# projects/markdownviewer/markdownviewer/__main__.py
from markdownviewer.app import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Manual verification (golden path)**

Run: `python -m markdownviewer` from `projects/markdownviewer/`

1. Ctrl+O, multi-select `sample-ok.md` and `sample-image.md` from Task 3 — confirm both open in separate tabs titled with their filenames.
2. Re-open `sample-ok.md` via Ctrl+O again — confirm it focuses the existing tab instead of creating a duplicate (Review Focus item 1).
3. Ctrl+W — confirm the active tab closes and the other remains.
4. File → Esci — confirm the app closes.

- [ ] **Step 3: Commit**

```bash
git add projects/markdownviewer/markdownviewer/app.py projects/markdownviewer/markdownviewer/__main__.py
git commit -m "feat: main window with File menu and tabbed notebook"
```

---

### Task 5: Update CODEMAP with actual structure

**Files:**
- Modify: `projects/markdownviewer/CODEMAP.md`

**Interfaces:** none (documentation only).

- [ ] **Step 1: Replace the "planned structure" codemap with the actual one**

Update `projects/markdownviewer/CODEMAP.md` to remove the "Nessun codice
ancora scritto" note and describe the real files created in Tasks 1-4
(`markdownviewer/render.py`, `markdownviewer/tab.py`, `markdownviewer/app.py`,
`markdownviewer/__main__.py`, `tests/test_render.py`), keeping the same
one-line-per-file style as the original.

- [ ] **Step 2: Commit**

```bash
git add projects/markdownviewer/CODEMAP.md
git commit -m "docs: update codemap to reflect implemented structure"
```
