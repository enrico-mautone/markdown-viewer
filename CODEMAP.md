# Codemap — markdownviewer

```
markdownviewer/
  CLAUDE.md                 Istruzioni di progetto per Claude Code
  CODEMAP.md                Questo file
  requirements.txt          Dipendenze runtime: tkinterweb, markdown
  requirements-dev.txt      requirements.txt + pytest
  requirements-build.txt    requirements.txt + pyinstaller
  build.ps1                 Costruisce MarkdownViewer.exe (venv temporanea +
                             PyInstaller --onefile --windowed) e lo copia
                             nella cartella da cui si lancia lo script —
                             vedi docs/build-eseguibile.md
  markdownviewer/
    __init__.py
    app.py                  Entry point applicativo: MarkdownViewerApp
                             (finestra principale, menu File con Apri
                             file.../Chiudi tab/Esci, ttk.Notebook che
                             ospita le tab; deduplica i file già aperti;
                             stile ttk custom con elemento "close" per il
                             bottone "x" su ogni tab; tooltip col path
                             completo al passaggio del mouse su una tab;
                             chiudere una tab fa anche destroy() del
                             widget, non solo forget(), per non perdere
                             memoria ad ogni chiusura; find-bar di ricerca
                             nella pagina — Ctrl+F o menu Modifica > Trova...
                             apre una barra in cima alla finestra, ricerca
                             case-insensitive con conteggio "n/tot",
                             ▲/▼ per prev/next con wraparound, Esc chiude e
                             pulisce gli highlight; usa find_text() di
                             tkinterweb sulla tab corrente con re.escape()
                             sul testo digitato [non è un campo regex] e
                             select 1-based [select=0 in tkinterweb ritorna
                             sempre 0 match]; il cambio tab resetta la
                             ricerca per non lasciare un conteggio riferito
                             alla tab precedente; barra con pulsante
                             "Ricarica", F5/Ctrl+R e voce File > Ricarica:
                             refresh_current_tab() ricarica la tab corrente
                             e, se la find-bar è aperta con del testo,
                             rilancia la ricerca sul contenuto nuovo — vedi
                             docs/ricarica-documento.md)
    __main__.py              Permette `python -m markdownviewer`
    render.py                Funzioni pure: file .md -> HTML (markdown
                             lib con estensione tables + CSS incorporato,
                             vedi docs/tabelle-markdown.md), senza dipendenze da
                             Tk — testate in isolamento in tests/. Legge
                             i file con utf-8-sig (accetta anche BOM) e
                             disattiva l'HTML grezzo nella libreria
                             markdown (preprocessor html_block e inline
                             pattern html deregistrati) così un file .md
                             non può aprire il browser di sistema o
                             caricare risorse remote senza un click
                             dell'utente
    tab.py                    MarkdownTab, wrapper attorno a un HtmlFrame
                             di tkinterweb per una singola tab: rendering,
                             messaggio d'errore se il file non è
                             leggibile, risoluzione path immagini
                             relativi via file_path.parent.as_uri() (NON
                             str(path): tkinterweb risolve i path relativi
                             con urljoin, che su Windows legge "C:" come
                             uno schema URL sconosciuto e li lascia non
                             risolti — vedi ruling nel ledger), apertura
                             link esterni nel browser di sistema
                             (on_link_click)
  tests/
    __init__.py
    test_render.py           Test su conversione md -> html e lettura
                             file (nessun test GUI automatizzato)
  manual_test/                Script di verifica manuale/smoke per le
                             parti GUI (tab.py, app.py) non coperte da
                             pytest — file di esempio + script eseguibili
                             che instanziano i widget e ne controllano il
                             comportamento (get_page_text, image_names,
                             webbrowser.open monkeypatchato, notebook
                             tabs) senza richiedere interazione manuale
                             col mouse
```

## Note

- Nessuna funzione di scrittura: `render.py` e `tab.py` non espongono mai
  un percorso che scriva sul file sorgente.
- `on_link_click` è passato come kwarg al costruttore di `HtmlFrame`
  (non è un metodo da chiamare dopo) — vedi ruling nel ledger del piano
  di implementazione.
- Vedi `docs/design-markdown-viewer.md` per la spec di design e
  `docs/superpowers/plans/2026-09-24-markdown-viewer.md` per il piano di
  implementazione.
- Vedi `docs/build-eseguibile.md` per come costruire l'eseguibile Windows.
- Vedi `docs/ricarica-documento.md` per il ricarico manuale del documento.
- La revisione finale (subagent fresco su tutto il branch, vedi ledger del
  piano) ha trovato e fatto correggere: immagini relative mai risolte su
  Windows (più il check di `manual_test/verify_tab.py` che lo dichiarava
  passato per errore), un file .md poteva aprire il browser di sistema
  senza alcun click (HTML grezzo passato non filtrato), file UTF-8 con BOM
  perdevano il primo titolo, tooltip/bottone "x" della spec non erano mai
  stati implementati. Dettagli e correzioni nel ledger.
