# Tabelle Markdown

Le tabelle erano fuori scope nella v1 (vedi [[design-markdown-viewer]]). Sono
state aggiunte perche' un file con tabelle veniva mostrato come testo con le
pipe (`| a | b |`) invece che come griglia.

## Come funziona

- `render.py` abilita l'estensione `tables` della libreria `markdown`
  (`markdown.Markdown(extensions=["tables"])`). Nessuna dipendenza nuova.
- L'allineamento delle colonne (`:--`, `:-:`, `--:`) la libreria lo emette come
  `style="text-align: ..."` inline, non come attributo `align`; Tkhtml (il motore
  di `tkinterweb`) lo rispetta.
- Il CSS incorporato in `render.py` da' ai bordi `border-collapse: collapse`,
  un bordo grigio a `th` e `td`, padding, e uno sfondo grigio all'intestazione.

## Sicurezza

La disattivazione dell'HTML grezzo (vedi [[design-markdown-viewer]] e il
commento in `render.py`) vale anche dentro le celle: `<script>` in una cella esce
come testo escapato. Lo verifica `test_markdown_to_html_table_cells_still_escape_raw_html`.

## Verifica

- Test unitari in `tests/test_render.py` (tabella, allineamento, escape nelle celle).
- `manual_test/sample-table.md` per provarla a mano. Verificata con uno
  screenshot del widget: griglia con bordi, intestazione in grassetto, tre
  allineamenti, grassetto/codice/link dentro le celle.

## Limiti

- Una cella non puo' contenere piu' righe o blocchi: e' il limite della sintassi
  Markdown a pipe, non dell'app.
