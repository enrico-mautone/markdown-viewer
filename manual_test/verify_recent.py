import re
import sys
import tempfile
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from markdownviewer.app import MarkdownViewerApp
from markdownviewer.recent import RECENT_LIMIT

PLACEHOLDER = "(nessun file recente)"
ENTRY_LABEL = re.compile(r"^\d+\. ")


def file_entries(app):
    menu = app._recent_menu
    last = menu.index("end")
    if last is None:
        return []
    labels = [menu.entrycget(i, "label") for i in range(last + 1) if menu.type(i) == "command"]
    return [label for label in labels if ENTRY_LABEL.match(label)]


def entry_index(app, name):
    menu = app._recent_menu
    for i in range(menu.index("end") + 1):
        if menu.type(i) == "command" and ENTRY_LABEL.match(menu.entrycget(i, "label")):
            if name in menu.entrycget(i, "label"):
                return i
    raise AssertionError(f"no recent entry for {name}")


def names(app):
    return [re.sub(r"^\d+\. ", "", label).split("  (")[0] for label in file_entries(app)]


def new_app(state):
    root = tk.Tk()
    root.geometry("600x300")
    return root, MarkdownViewerApp(root, recent_path=state)


with tempfile.TemporaryDirectory() as tmp:
    tmp_dir = Path(tmp)
    state = tmp_dir / "state" / "recent.json"
    docs = []
    for i in range(12):
        doc = tmp_dir / f"doc{i}.md"
        doc.write_text(f"# Documento {i}\n", encoding="utf-8")
        docs.append(doc.resolve())

    root, app = new_app(state)

    # The "Recenti" menu sits between File and Modifica
    menubar = root.nametowidget(root["menu"])
    titles = [
        menubar.entrycget(i, "label")
        for i in range(menubar.index("end") + 1)
        if menubar.type(i) == "cascade"
    ]
    assert titles.index("Recenti") == titles.index("File") + 1, titles
    assert titles.index("Recenti") < titles.index("Modifica"), titles
    print(f"[menu] top-level menus: {titles}")

    # Empty list: a disabled placeholder, nothing to click
    menu = app._recent_menu
    assert menu.index("end") == 0
    assert menu.entrycget(0, "label") == PLACEHOLDER
    assert str(menu.entrycget(0, "state")) == "disabled"
    print("[empty] disabled placeholder shown")

    # Newest first
    for doc in docs[:3]:
        app._open_one(doc)
    root.update()
    assert names(app) == ["doc2.md", "doc1.md", "doc0.md"], names(app)
    print(f"[order] newest first: {names(app)}")

    # Reopening a file moves it to the top, no duplicate
    app._open_one(docs[0])
    root.update()
    assert names(app) == ["doc0.md", "doc2.md", "doc1.md"], names(app)
    print(f"[reopen] moved to the top without duplicating: {names(app)}")

    # Circular: after 10 the oldest drops out
    for doc in docs[3:]:
        app._open_one(doc)
    root.update()
    shown = names(app)
    assert len(shown) == RECENT_LIMIT == 10, shown
    assert shown[0] == "doc11.md", shown
    assert "doc1.md" not in shown and "doc2.md" not in shown, shown
    print(f"[circular] {len(shown)} entries, newest {shown[0]}, oldest {shown[-1]}")

    # Persisted across runs
    root.destroy()
    root, app = new_app(state)
    assert names(app) == shown, (names(app), shown)
    print("[persist] a new app instance shows the same list")

    # Clicking an entry opens that file (and moves it to the top)
    for tab_id in list(app.notebook.tabs()):
        app._close_tab(tab_id)
    root.update()
    assert app.notebook.tabs() == ()
    app._recent_menu.invoke(entry_index(app, "doc5.md"))
    root.update()
    assert len(app.notebook.tabs()) == 1
    assert app.notebook.tab(app.notebook.tabs()[0], "text") == "doc5.md"
    assert names(app)[0] == "doc5.md"
    print("[open] clicking an entry opens that file and moves it to the top")

    # A recent whose file is gone: removed from the list, the tab explains why
    docs[7].unlink()
    app._recent_menu.invoke(entry_index(app, "doc7.md"))
    root.update()
    assert "doc7.md" not in names(app), names(app)
    assert "File non trovato" in app._current_tab().get_page_text()
    print("[missing] vanished file dropped from the list, error shown in its tab")

    # A file that does not exist is never added to the list
    before = names(app)
    app._open_one(tmp_dir / "never-existed.md")
    root.update()
    assert names(app) == before, names(app)
    print("[nonexistent] opening a missing path does not pollute the list")

    # "Svuota elenco" clears the list and the saved state
    menu = app._recent_menu
    clear_index = next(
        i for i in range(menu.index("end") + 1)
        if menu.type(i) == "command" and menu.entrycget(i, "label") == "Svuota elenco"
    )
    menu.invoke(clear_index)
    root.update()
    assert menu.entrycget(0, "label") == PLACEHOLDER and menu.index("end") == 0
    root.destroy()
    root, app = new_app(state)
    assert app._recent_menu.entrycget(0, "label") == PLACEHOLDER
    print("[clear] list emptied, and it stays empty after a restart")
    root.destroy()

print("ALL RECENT CASES PASSED")
