# File recenti

Il menu **Recenti** (tra File e Modifica) elenca gli ultimi 10 file aperti, per
riaprirli con un click senza passare dal dialog.

## Comportamento

- **Ordine**: dal piu' recente (1.) al piu' vecchio. Ogni voce mostra il nome del
  file e, tra parentesi, la cartella, per distinguere file con lo stesso nome.
- **Circolare**: l'elenco tiene al massimo 10 file. Aprendo l'11. esce il piu'
  vecchio e restano gli ultimi 10.
- **Riapertura**: un file gia' in elenco, se lo riapri, sale in cima senza
  comparire due volte. Vale anche se la sua tab e' gia' aperta.
- **Click su una voce**: apre il file in una tab (o porta in primo piano quella
  gia' aperta) e lo sposta in cima.
- **Elenco vuoto**: una voce grigia "(nessun file recente)", non cliccabile.
- **Svuota elenco**: ultima voce del menu, cancella l'elenco e il file di stato.
- **File sparito**: cliccando una voce il cui file non esiste piu', la voce viene
  tolta dall'elenco e la tab mostra "File non trovato", come per ogni altro file
  mancante.
- **Solo file esistenti**: un percorso che non esiste non entra mai nell'elenco.

## Persistenza e scope

L'elenco si conserva tra una sessione e l'altra in
`%APPDATA%\MarkdownViewer\recent.json` (se `APPDATA` non e' definita:
`~/.config/MarkdownViewer/recent.json`).
E' l'unico file che l'app scrive: l'app continua a non modificare mai i `.md`
aperti, vedi [[design-markdown-viewer]].

Se il file di stato manca, e' corrotto o non e' scrivibile, l'app non va in crash:
parte con l'elenco vuoto, oppure lo tiene solo in memoria per quella sessione, e
scrive un avviso nel log (`logging`). La scrittura passa da un file temporaneo e
`os.replace`, cosi' un crash a meta' non lascia un JSON troncato.

## Struttura

- `recent.py`: `RecentFiles`, logica pura senza Tk (ordine, limite, persistenza),
  testata in `tests/test_recent.py`.
- `app.py`: costruisce il menu e registra i file in `_open_one`, vedi
  [[ricarica-documento]] per l'altra aggiunta alla stessa barra dei menu.
- `MarkdownViewerApp(root, recent_path=...)` accetta un percorso alternativo per il
  file di stato: gli script di `manual_test/` ne usano uno temporaneo cosi' non
  sporcano l'elenco reale.

## Verifica

`manual_test/verify_recent.py` copre: posizione del menu, elenco vuoto, ordine,
riapertura, circolarita' a 10, persistenza tra due istanze, click su una voce,
file sparito, percorso inesistente, svuota elenco.
