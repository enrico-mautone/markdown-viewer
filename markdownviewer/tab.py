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
        super().__init__(parent, messages_enabled=False, on_link_click=self._handle_link_click)
        self.file_path = file_path
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

        # as_uri() (not str(path)) so tkinterweb's urljoin-based resolver
        # recognizes the base as a URL — a plain "C:\...\" base makes
        # urljoin read "C:" as an unknown scheme and relative images never
        # resolve.
        self.load_html(html, base_url=self.file_path.parent.as_uri() + "/")

    def _handle_link_click(self, url: str):
        if url.startswith("http://") or url.startswith("https://"):
            webbrowser.open(url)
