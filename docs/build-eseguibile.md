# Build dell'eseguibile Windows

Il packaging era fuori scope nella v1 (vedi [[design-markdown-viewer]]); questo
documento descrive come si costruisce `MarkdownViewer.exe` ora che e' stato
richiesto.

## Uso

Da PowerShell, posizionati nella cartella dove vuoi ritrovare l'exe e lancia lo
script indicando il suo percorso:

```powershell
cd C:\Users\me\Desktop
powershell -ExecutionPolicy Bypass -File C:\path\to\markdown-viewer\build.ps1
```

`MarkdownViewer.exe` viene copiato nella cartella corrente (quella da cui
lanci lo script), non in quella del repo. `-ExecutionPolicy Bypass` serve
perche' la policy predefinita di Windows blocca l'esecuzione di file `.ps1`.

Requisiti: Python 3 nel `PATH`. Non serve installare nient'altro a mano.

## Cosa fa lo script

1. Crea una venv temporanea nella cartella temp di sistema.
2. Installa `requirements-build.txt` (dipendenze runtime + PyInstaller) nella venv.
3. Esegue PyInstaller con `--onefile --windowed --collect-all tkinterweb`.
4. Copia l'exe nella cartella corrente.
5. Cancella la venv e i file intermedi, anche in caso di errore.

## Scelte

- **venv temporanea**: PyInstaller non finisce nel Python globale e il repo non
  si sporca di cartelle `build/` o file `.spec`.
- **`--collect-all tkinterweb`**: `tkinterweb` carica a runtime una libreria
  nativa (Tkhtml) che PyInstaller non rileva da solo. Senza questo flag l'exe
  parte ma fallisce quando apre la prima tab.
- **`--onefile`**: un solo file da distribuire; l'avvio e' un po' piu' lento
  perche' si decomprime in una cartella temporanea.
- **`--windowed`**: nessuna finestra console dietro l'app.

## Limiti noti

- L'exe non e' firmato: SmartScreen puo' mostrare "Windows ha protetto il PC" al
  primo avvio, e alcuni antivirus possono segnalarlo per errore.
- L'exe e' valido solo per Windows, con la versione di Python usata per la build.
