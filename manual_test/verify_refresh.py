import sys
import tempfile
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from markdownviewer.app import MarkdownViewerApp


def build_doc(marker: str) -> str:
    paragraphs = "\n\n".join(f"Paragrafo numero {i}" for i in range(200))
    return f"# {marker}\n\n{paragraphs}\n"


def page_text(tab) -> str:
    return tab.get_page_text()


with tempfile.TemporaryDirectory() as tmp:
    doc = Path(tmp, "doc.md")
    doc.write_text(build_doc("VERSIONE-1"), encoding="utf-8")
    doc = doc.resolve()

    root = tk.Tk()
    root.geometry("700x400")
    app = MarkdownViewerApp(root)

    # No open tab: pressing refresh must be a harmless no-op
    app._refresh_button.invoke()
    root.update()
    print("[no-tab] refresh with no open tab does nothing")

    app._open_one(doc)
    root.update()
    tab = app._current_tab()
    assert "VERSIONE-1" in page_text(tab)

    # Refresh picks up the new file content and keeps the scroll position
    tab.yview_moveto(0.5)
    root.update()
    scrolled_before = tab.html.yview()[0]
    assert scrolled_before > 0.3, f"test setup: expected a scrolled page, got {scrolled_before}"

    doc.write_text(build_doc("VERSIONE-2"), encoding="utf-8")
    app._refresh_button.invoke()
    root.update()
    text = page_text(tab)
    assert "VERSIONE-2" in text and "VERSIONE-1" not in text, text[:80]
    scrolled_after = tab.html.yview()[0]
    assert abs(scrolled_after - scrolled_before) < 0.05, (scrolled_before, scrolled_after)
    assert len(app.notebook.tabs()) == 1, "refresh must not open a second tab"
    print(f"[refresh] new content shown, scroll kept ({scrolled_before:.2f} -> {scrolled_after:.2f}), still one tab")

    # Shortcuts are bound
    assert root.bind("<F5>"), "F5 not bound"
    assert root.bind("<Control-r>"), "Ctrl+R not bound"
    print("[shortcuts] F5 and Ctrl+R bound")

    # File deleted: the tab shows the error page, then recovers when the file is back
    doc.unlink()
    app._refresh_button.invoke()
    root.update()
    assert "File non trovato" in page_text(tab), page_text(tab)[:120]
    doc.write_text(build_doc("VERSIONE-3"), encoding="utf-8")
    app._refresh_button.invoke()
    root.update()
    assert "VERSIONE-3" in page_text(tab)
    print("[missing-file] error page shown, then recovered once the file reappeared")

    # An open search is re-applied to the refreshed content
    app._open_find_bar()
    app._find_entry.delete(0, "end")
    app._find_entry.insert(0, "Paragrafo")
    app._run_search(reset=True)
    root.update()
    assert app._find_total == 200, app._find_total
    doc.write_text(build_doc("VERSIONE-4") + "\n\nParagrafo extra\n", encoding="utf-8")
    app._refresh_button.invoke()
    root.update()
    assert app._find_total == 201, app._find_total
    print(f"[search] open search re-applied after refresh: {app._find_total} matches")

    root.destroy()

print("ALL REFRESH CASES PASSED")
