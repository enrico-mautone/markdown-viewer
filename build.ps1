<#
.SYNOPSIS
Costruisce MarkdownViewer.exe e lo copia nella cartella da cui lanci lo script.

.EXAMPLE
cd C:\Users\me\Desktop
powershell -ExecutionPolicy Bypass -File C:\path\to\markdown-viewer\build.ps1
#>
$ErrorActionPreference = 'Stop'

$repoRoot = $PSScriptRoot
$outputDir = (Get-Location).Path
$exeName = 'MarkdownViewer'
$workDir = Join-Path ([System.IO.Path]::GetTempPath()) ('markdownviewer-build-' + [guid]::NewGuid().ToString('N'))

function Invoke-Checked {
    param([string]$Description, [scriptblock]$Command)
    Write-Host "==> $Description"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description fallito (exit code $LASTEXITCODE)"
    }
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python non trovato nel PATH. Installa Python 3 e riprova.'
}

try {
    New-Item -ItemType Directory -Path $workDir | Out-Null
    $venvDir = Join-Path $workDir 'venv'
    $venvPython = Join-Path $venvDir 'Scripts\python.exe'

    Invoke-Checked 'Creo ambiente virtuale temporaneo' {
        python -m venv $venvDir
    }
    Invoke-Checked 'Installo dipendenze di build' {
        & $venvPython -m pip install --quiet --disable-pip-version-check -r (Join-Path $repoRoot 'requirements-build.txt')
    }
    Invoke-Checked 'Costruisco l''eseguibile con PyInstaller' {
        & $venvPython -m PyInstaller --noconfirm --clean --onefile --windowed `
            --name $exeName --collect-all tkinterweb --paths $repoRoot `
            --distpath (Join-Path $workDir 'dist') `
            --workpath (Join-Path $workDir 'build') `
            --specpath $workDir `
            (Join-Path $repoRoot 'markdownviewer\__main__.py')
    }

    $builtExe = Join-Path $workDir "dist\$exeName.exe"
    Copy-Item -Path $builtExe -Destination $outputDir -Force
    Write-Host "Fatto: $(Join-Path $outputDir "$exeName.exe")"
}
finally {
    if (Test-Path $workDir) {
        Remove-Item -Recurse -Force $workDir -ErrorAction SilentlyContinue
    }
}
