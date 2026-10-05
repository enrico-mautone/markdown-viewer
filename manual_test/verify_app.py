import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from markdownviewer.app import MarkdownViewerApp

HERE = Path(__file__).resolve().parent

root = tk.Tk()
app = MarkdownViewerApp(root)

ok_path = (HERE / "sample-ok.md").resolve()
image_path = (HERE / "sample-image.md").resolve()

# Golden path: open two distinct files -> two tabs
app._open_one(ok_path)
app._open_one(image_path)
root.update()
tabs = app.notebook.tabs()
assert len(tabs) == 2, f"expected 2 tabs, got {len(tabs)}"
titles = [app.notebook.tab(t, "text") for t in tabs]
assert titles == ["sample-ok.md", "sample-image.md"], titles
print(f"[open] two distinct files -> two tabs: {titles}")

# Re-open same file -> focuses existing tab, no duplicate
app._open_one(ok_path)
root.update()
tabs_after_reopen = app.notebook.tabs()
assert len(tabs_after_reopen) == 2, f"expected still 2 tabs after reopen, got {len(tabs_after_reopen)}"
assert app.notebook.select() == app._open_paths[ok_path]
print("[reopen] same file focuses existing tab, no duplicate")

# Close current tab (the reopened/selected sample-ok.md) -> one tab remains
app.close_current_tab()
root.update()
tabs_after_close = app.notebook.tabs()
assert len(tabs_after_close) == 1, f"expected 1 tab after close, got {len(tabs_after_close)}"
remaining_title = app.notebook.tab(tabs_after_close[0], "text")
assert remaining_title == "sample-image.md", remaining_title
assert ok_path not in app._open_paths
print(f"[close] tab closed, remaining: {remaining_title}")

root.destroy()

# ttk::notebook has no "bbox" subcommand (Notebook.bbox() actually resolves
# to the unrelated Frame.grid_bbox() and always returns zeros) — element
# positions are found by scanning identify() across a row of the tab strip.
TAB_ROW_Y = 10


def _find_x(notebook, wanted_element, max_x=300):
    for x in range(max_x):
        if wanted_element in notebook.identify(x, TAB_ROW_Y):
            return x
    raise AssertionError(f"no {wanted_element!r} element found in first {max_x}px")


# Tooltip shows the tab's full path (spec: "il tooltip il path completo")
root = tk.Tk()
app = MarkdownViewerApp(root)
app._open_one(ok_path)
root.update()
label_x = _find_x(app.notebook, "label")
event = type(
    "Event",
    (),
    {"widget": app.notebook, "x": label_x, "y": TAB_ROW_Y, "x_root": label_x, "y_root": TAB_ROW_Y},
)()
app._on_tab_motion(event)
assert app._tooltip is not None and app._tooltip_label is not None
assert app._tooltip_label.cget("text") == str(ok_path), app._tooltip_label.cget("text")
print(f"[tooltip] shows full path: {app._tooltip_label.cget('text')}")
root.destroy()

# "x" close button actually closes the tab (spec: 'bottone "x" sulla tab')
root = tk.Tk()
app = MarkdownViewerApp(root)
app._open_one(ok_path)
root.update()
close_x = _find_x(app.notebook, "close")
click_event = type("Event", (), {"widget": app.notebook, "x": close_x, "y": TAB_ROW_Y})()
app._on_tab_click(click_event)
root.update()
assert app.notebook.tabs() == (), f"expected tab closed, got {app.notebook.tabs()}"
print("[close-button] clicking the 'x' element closes the tab")
root.destroy()

# --- In-page search (Ctrl+F / find bar) ---

# sample-search.md has three case-varied occurrences of "apple" to exercise
# case-insensitive matching and next/prev wraparound.
search_path = (HERE / "sample-search.md").resolve()

# Ctrl+F opens the find bar and focuses the entry
root = tk.Tk()
app = MarkdownViewerApp(root)
app._open_one(search_path)
root.update()
assert not app._find_bar.winfo_ismapped()
app._open_find_bar()
root.update()
assert app._find_bar.winfo_ismapped()
assert app.root.focus_get() == app._find_entry
print("[find-open] Ctrl+F opens the bar and focuses the entry")

# Typing a match updates the count and highlights
app._find_entry.insert(0, "apple")
app._run_search(reset=True)
root.update()
assert app._find_total == 3, app._find_total
assert app._find_index == 1
assert app._find_count_label.cget("text") == "1/3", app._find_count_label.cget("text")
print(f"[find-match] 'apple' found case-insensitively: {app._find_count_label.cget('text')}")

# Text not present -> "Nessun risultato", no crash
app._find_entry.delete(0, "end")
app._find_entry.insert(0, "zzz-not-in-page-zzz")
app._run_search(reset=True)
root.update()
assert app._find_total == 0
assert app._find_count_label.cget("text") == "Nessun risultato"
print("[find-nomatch] absent text shows 'Nessun risultato'")

# Regex special characters in the search box are treated literally
app._find_entry.delete(0, "end")
app._find_entry.insert(0, "(")
app._run_search(reset=True)
root.update()  # must not raise
print("[find-literal] regex-special character searched literally without crashing")

# Next/prev wrap around
app._find_entry.delete(0, "end")
app._find_entry.insert(0, "apple")
app._run_search(reset=True)
root.update()
total = app._find_total
assert total == 3, total
app._find_prev()
root.update()
assert app._find_index == total, f"expected wraparound to last match ({total}), got {app._find_index}"
app._find_next()
root.update()
assert app._find_index == 1, f"expected wraparound to first match, got {app._find_index}"
print(f"[find-wrap] prev/next wrap around across {total} matches")

# Esc closes the bar and clears the highlight/count
app._find_entry.event_generate("<Escape>")
root.update()
assert not app._find_bar.winfo_ismapped()
assert app._find_total == 0
assert app._find_count_label.cget("text") == ""
print("[find-close] Esc closes the bar and clears the search")
root.destroy()

# Switching tabs resets the search (no stale count/highlight on the new tab)
root = tk.Tk()
app = MarkdownViewerApp(root)
app._open_one(search_path)
app._open_one(image_path)
root.update()
app._open_find_bar()
app._find_entry.insert(0, "With")  # present in sample-image.md, the active tab
app._run_search(reset=True)
root.update()
assert app._find_total >= 1, app._find_total
app.notebook.select(app._open_paths[search_path])
root.update()
assert app._find_total == 0, "expected search state reset after tab switch"
assert app._find_count_label.cget("text") == ""
print("[find-tab-switch] switching tabs resets the search state")
root.destroy()

print("ALL APP CASES PASSED")
