import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from markdownviewer.tab import MarkdownTab


def _make_close_icon(background: str, mark: str) -> tk.PhotoImage:
    """Draw a small 'x' glyph as a PhotoImage (no Pillow dependency)."""
    size = 12
    icon = tk.PhotoImage(width=size, height=size)
    icon.put(background, to=(0, 0, size, size))
    for i in range(2, size - 2):
        icon.put(mark, (i, i))
        icon.put(mark, (size - 1 - i, i))
    return icon


class MarkdownViewerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Markdown Viewer")
        self.root.geometry("900x700")

        # tkinter needs a reference kept alive for PhotoImages passed to
        # ttk.Style, otherwise they're garbage-collected off the tab.
        self._close_icon_normal = _make_close_icon("#d9d9d9", "#555555")
        self._close_icon_active = _make_close_icon("#e81123", "#ffffff")
        self._install_closable_tab_style()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<ButtonRelease-1>", self._on_tab_click)
        self.notebook.bind("<Motion>", self._on_tab_motion)
        self.notebook.bind("<Leave>", lambda _event: self._hide_tooltip())

        self._open_paths: dict[Path, str] = {}  # resolved path -> notebook tab id
        self._tab_paths: dict[str, Path] = {}  # notebook tab id -> resolved path
        self._tooltip: tk.Toplevel | None = None
        self._tooltip_label: tk.Label | None = None

        self._build_menu()
        self._build_find_bar()
        self.notebook.bind("<<NotebookTabChanged>>", lambda _event: self._on_tab_changed())
        self.root.bind("<Control-o>", lambda _event: self.open_files())
        self.root.bind("<Control-w>", lambda _event: self.close_current_tab())
        self.root.bind("<Control-f>", lambda _event: self._open_find_bar())

    def _install_closable_tab_style(self):
        # Adds a "close" element to the tab layout (spec: bottone "x" sulla
        # tab). ttk.Notebook has no built-in close button, so the element is
        # registered by hand and located later via identify() on click.
        style = ttk.Style(self.root)
        style.element_create(
            "close",
            "image",
            self._close_icon_normal,
            ("active", self._close_icon_active),
            border=4,
            sticky="",
        )
        style.layout(
            "TNotebook.Tab",
            [
                (
                    "TNotebook.tab",
                    {
                        "sticky": "nswe",
                        "children": [
                            (
                                "TNotebook.padding",
                                {
                                    "sticky": "nswe",
                                    "children": [
                                        (
                                            "TNotebook.focus",
                                            {
                                                "sticky": "nswe",
                                                "children": [
                                                    ("TNotebook.label", {"side": "left", "sticky": ""}),
                                                    ("TNotebook.close", {"side": "left", "sticky": ""}),
                                                ],
                                            },
                                        )
                                    ],
                                },
                            )
                        ],
                    },
                )
            ],
        )

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Apri file...", accelerator="Ctrl+O", command=self.open_files)
        file_menu.add_command(label="Chiudi tab", accelerator="Ctrl+W", command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Trova...", accelerator="Ctrl+F", command=self._open_find_bar)
        menubar.add_cascade(label="Modifica", menu=edit_menu)

        self.root.config(menu=menubar)

    def _build_find_bar(self):
        # Docked at the top of the window, hidden until Ctrl+F (spec:
        # "ricerca nella pagina... con bottone e dialog di ricerca o
        # CTRL+F"). Not packed here: _open_find_bar() packs it on demand.
        self._find_bar = ttk.Frame(self.root)
        ttk.Label(self._find_bar, text="Trova:").pack(side="left", padx=(4, 2))
        self._find_entry = ttk.Entry(self._find_bar)
        self._find_entry.pack(side="left", fill="x", expand=True, padx=2)
        self._find_entry.bind("<KeyRelease>", self._on_find_key_release)
        self._find_entry.bind("<Return>", lambda _event: self._find_next())
        self._find_entry.bind("<Shift-Return>", lambda _event: self._find_prev())
        self._find_entry.bind("<Escape>", lambda _event: self._close_find_bar())
        self._find_count_label = ttk.Label(self._find_bar, text="", width=12)
        self._find_count_label.pack(side="left", padx=2)
        ttk.Button(self._find_bar, text="▲", width=2, command=self._find_prev).pack(side="left")
        ttk.Button(self._find_bar, text="▼", width=2, command=self._find_next).pack(side="left")
        ttk.Button(self._find_bar, text="✕", width=2, command=self._close_find_bar).pack(
            side="left", padx=(2, 4)
        )
        self._find_index = 0  # 1-based index of the currently selected match
        self._find_total = 0

    def _current_tab(self) -> MarkdownTab | None:
        selected = self.notebook.select()
        if not selected:
            return None
        return self.root.nametowidget(selected)

    def _open_find_bar(self):
        if not self._find_bar.winfo_ismapped():
            self._find_bar.pack(side="top", fill="x", before=self.notebook)
        self._find_entry.focus_force()
        self._find_entry.select_range(0, "end")
        if self._find_entry.get():
            self._run_search(reset=False)

    def _close_find_bar(self):
        if self._find_bar.winfo_ismapped():
            self._find_bar.pack_forget()
        self._clear_search()

    def _on_tab_changed(self):
        # A search's highlights and match index only make sense for the tab
        # they were run on; switching tabs resets them rather than leaving
        # a stale count pointing at the previous tab's matches.
        if self._find_bar.winfo_ismapped():
            self._clear_search(keep_text=True)

    def _clear_search(self, keep_text: bool = False):
        tab = self._current_tab()
        if tab is not None:
            tab.find_text("", select=1)
        self._find_index = 0
        self._find_total = 0
        self._find_count_label.config(text="")
        if not keep_text:
            self._find_entry.delete(0, "end")

    def _on_find_key_release(self, event):
        if event.keysym in ("Return", "Escape", "Up", "Down"):
            return
        self._run_search(reset=True)

    def _find_next(self):
        self._step_search(1)

    def _find_prev(self):
        self._step_search(-1)

    def _step_search(self, direction: int):
        if self._find_total == 0:
            self._run_search(reset=True)
            return
        # Wrap around in both directions: (index - 1 + direction) % total
        # keeps a 0-based rotation, then +1 restores the 1-based index
        # find_text() expects.
        self._find_index = (self._find_index - 1 + direction) % self._find_total + 1
        self._run_search(reset=False)

    def _run_search(self, reset: bool):
        tab = self._current_tab()
        text = self._find_entry.get()
        if tab is None or not text:
            self._find_total = 0
            self._find_index = 0
            self._find_count_label.config(text="")
            if tab is not None:
                tab.find_text("", select=1)
            return

        if reset:
            self._find_index = 1

        # re.escape: the search box is a plain-text find, not a regex
        # field — tkinterweb's find_text() treats the string as a regex,
        # so unescaped input would make e.g. "(" or "." behave unexpectedly.
        pattern = re.escape(text)
        # select is 1-indexed in tkinterweb; select=0 silently returns 0
        # matches regardless of real matches (see tab.py's find_text usage).
        total = tab.find_text(pattern, select=max(self._find_index, 1), ignore_case=True, highlight_all=True)
        self._find_total = total
        self._find_index = 0 if total == 0 else min(max(self._find_index, 1), total)
        self._update_find_count()

    def _update_find_count(self):
        if self._find_total == 0:
            self._find_count_label.config(text="Nessun risultato")
        else:
            self._find_count_label.config(text=f"{self._find_index}/{self._find_total}")

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
        self._tab_paths[tab_id] = path
        self.notebook.select(tab)

    def close_current_tab(self):
        selected = self.notebook.select()
        if selected:
            self._close_tab(selected)

    def _close_tab(self, tab_id: str):
        self.notebook.forget(tab_id)
        self._open_paths = {p: tid for p, tid in self._open_paths.items() if tid != tab_id}
        self._tab_paths.pop(tab_id, None)
        self._hide_tooltip()
        # forget() only hides the tab; without destroy() the MarkdownTab
        # (and its HtmlFrame/images) stays alive for the app's whole
        # lifetime, leaking memory on every close.
        self.root.nametowidget(tab_id).destroy()

    def _on_tab_click(self, event):
        element = event.widget.identify(event.x, event.y)
        if "close" not in element:
            return
        index = event.widget.index(f"@{event.x},{event.y}")
        tabs = event.widget.tabs()
        if index < len(tabs):
            self._close_tab(tabs[index])

    def _on_tab_motion(self, event):
        element = event.widget.identify(event.x, event.y)
        if "label" not in element:
            self._hide_tooltip()
            return
        tabs = event.widget.tabs()
        index = event.widget.index(f"@{event.x},{event.y}")
        if index >= len(tabs):
            self._hide_tooltip()
            return
        path = self._tab_paths.get(tabs[index])
        if path is None:
            self._hide_tooltip()
            return
        self._show_tooltip(event.x_root, event.y_root, str(path))

    def _show_tooltip(self, x_root: int, y_root: int, text: str):
        if self._tooltip is None:
            self._tooltip = tk.Toplevel(self.root)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip_label = tk.Label(
                self._tooltip,
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 8),
            )
            self._tooltip_label.pack()
        self._tooltip_label.config(text=text)
        self._tooltip.wm_geometry(f"+{x_root + 12}+{y_root + 12}")
        self._tooltip.deiconify()

    def _hide_tooltip(self):
        if self._tooltip is not None:
            self._tooltip.withdraw()


def main():
    root = tk.Tk()
    MarkdownViewerApp(root)
    root.mainloop()
