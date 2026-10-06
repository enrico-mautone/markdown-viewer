# Design — markdownviewer (v1)

**Data:** 2026-09-24
**Stato:** approvato per implementazione

## Obiettivo

App desktop Python per aprire e visualizzare file Markdown, in sola
lettura. Nessuna scrittura o modifica del file sorgente, in nessun punto
dell'applicazione.

## Scelte confermate (da brainstorming con Enrico)

| Decisione | Scelta | Alternativa scartata |
|---|---|---|
| Toolkit UI | `tkinter` (stdlib) | PySide6/PyQt6 + QWebEngineView (troppo pesante da installare) |
| Rendering HTML | `tkinterweb` (HtmlFrame) | Motore browser integrato — non necessario per lo scope |
| Conversione MD→HTML | libreria `markdown` | — |
| Multi-file | una tab per file (`ttk.Notebook`) | sidebar+area unica, finestre multiple |
| Apertura file | solo dialog "Apri file" (Ctrl+O, multi-selezione) | drag&drop, argomenti CLI |
| Scope Markdown | base (titoli, liste, grassetto/corsivo, link, immagini, code block senza syntax highlighting) + tabelle (aggiunte dopo la v1, vedi [[tabelle-markdown]]) | GitHub-flavored completo (task-list, syntax highlighting colorato) |

## Architettura

```
markdownviewer/app.py      entry point, finestra, menu File, ttk.Notebook
markdownviewer/render.py   funzioni pure: file .md -> HTML (no dipendenze Tk)
markdownviewer/tab.py      wrapper per una singola tab (HtmlFrame + gestione
                            errori + link esterni + path immagini relativi)
```

Vedi [[CODEMAP]] per il dettaglio directory.

## Comportamento

- **Apertura**: File → Apri file... (Ctrl+O) apre `filedialog.askopenfilenames`
  con filtro `*.md;*.markdown`. Ogni file selezionato apre una nuova tab, il
  titolo tab è il nome file, il tooltip il path completo.
- **File già aperto**: se il path è già in una tab esistente, l'app porta il
  focus su quella tab invece di duplicarla.
- **Chiusura**: bottone "x" sulla tab o Ctrl+W chiude la tab corrente. File →
  Esci chiude l'app.
- **Rendering**: `render.py` converte il testo markdown in HTML con
  `markdown.markdown()`, avvolto in un piccolo template HTML con CSS
  incorporato (font leggibile, stile per code block, blockquote, immagini
  responsive). Il path base per le immagini relative è la cartella del file
  `.md` (`base_url` di tkinterweb).
- **Link esterni**: click su un link `http(s)://` apre il browser di sistema
  via `webbrowser.open()`, non naviga dentro l'app.
- **Errori**: file non trovato, non leggibile (permessi) o con encoding non
  UTF-8 → la tab mostra un messaggio di errore leggibile invece del render;
  l'app resta utilizzabile e le altre tab non sono impattate. Markdown
  malformato non genera errori bloccanti: la libreria `markdown` è
  tollerante e renderizza il meglio possibile.

## Esplicitamente fuori scope (v1)

- Salvataggio o modifica del file sorgente (nessuna area editabile in tutta
  l'app, per costruzione).
- Drag & drop, argomenti da riga di comando.
- Task-list, strikethrough, syntax highlighting colorato nei code
  block.
- Auto-reload se il file cambia su disco mentre è aperto.
- Packaging/installer (es. PyInstaller) — non richiesto in questa fase.

## Testing

- Test automatici solo su logica pura in `render.py` (conversione md→html,
  gestione file non trovato / encoding errato) — nessun test GUI
  automatizzato.
- Verifica manuale: aprire più file di esempio (titoli, liste, link,
  immagini, blocco di codice) in tab diverse, verificare apertura link
  esterni nel browser e messaggio d'errore su file mancante.

## Dipendenze

`requirements.txt`: `tkinterweb`, `markdown`. Nessuna altra dipendenza
esterna.
