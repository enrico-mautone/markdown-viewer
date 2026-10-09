# Ricarica del documento

Permette di rileggere dal disco il file aperto in una tab senza chiuderlo e
riaprirlo, per esempio dopo averlo modificato in un altro editor. E' un
ricarico **manuale**: l'auto-reload quando il file cambia resta fuori scope
(vedi [[design-markdown-viewer]]).

## Come si usa

- Pulsante **Ricarica** nella barra sotto il menu.
- **F5** o **Ctrl+R**.
- Menu **File → Ricarica**.

Agisce sulla tab corrente. Con nessuna tab aperta non fa niente.

## Come funziona

- `MarkdownTab.reload()` (`tab.py`) rilegge il file con lo stesso `_load()` usato
  all'apertura, quindi gli errori (file mancante, non UTF-8, permessi) vengono
  mostrati nella tab come alla prima apertura, senza eccezioni.
- Prima del ricarico salva la posizione di scroll e dopo la ripristina:
  `load_html()` riporterebbe sempre il documento in cima. La posizione si legge
  con `html.yview()[0]`, perche' `HtmlFrame.yview()` restituisce `None`, e si
  ripristina con `yview_moveto()`. E' una frazione dell'altezza, quindi se il
  documento cambia molto di lunghezza il punto esatto si sposta.
- `MarkdownViewerApp.refresh_current_tab()` (`app.py`) chiama `reload()` e, se la
  barra di ricerca (vedi Ctrl+F) e' aperta con del testo, rilancia la ricerca sul
  contenuto nuovo, perche' il ricarico cancella gli evidenziati.

## Se il file sparisce

Il ricarico mostra il messaggio "File non trovato" nella tab. Ripristinando il
file e premendo di nuovo Ricarica, il documento torna visibile.

## Verifica

`manual_test/verify_refresh.py` copre: nessuna tab aperta, contenuto aggiornato,
scroll mantenuto, nessuna tab duplicata, tasti F5 e Ctrl+R associati, file
cancellato e poi ripristinato, ricerca riapplicata dopo il ricarico.
