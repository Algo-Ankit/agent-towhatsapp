# Windows PowerShell: create an isolated virtual environment in .venv and install deps.
# Your global Python is never touched.
# Run:  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Test-Py($exe, $extra) {
    try {
        $args = @($extra) + @("-c", "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)") | Where-Object { $_ }
        & $exe @args 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

$exe = $null; $extra = $null
if (Test-Py "py" "-3") { $exe = "py"; $extra = "-3" }
elseif (Test-Py "python" $null) { $exe = "python" }
if (-not $exe) { Write-Host "Python 3.10+ not found. Install it from python.org and tick 'Add python.exe to PATH'."; exit 1 }

if (-not (Test-Path ".venv")) {
    Write-Host "Creating .venv..."
    $venvArgs = @($extra) + @("-m", "venv", ".venv") | Where-Object { $_ }
    & $exe @venvArgs
}

& .\.venv\Scripts\python.exe -m pip install -q --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

Write-Host ""
Write-Host "Done. Environment is in .venv (isolated from your global Python)."
Write-Host "Activate it:   .\.venv\Scripts\Activate.ps1"
Write-Host "Start server:  uvicorn app.main:app --port 8000"
Write-Host "Chat (2nd terminal, also activated):  python scripts\simulate.py"
