$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python -m venv .venv-build
& .\.venv-build\Scripts\python -m pip install --upgrade pip
& .\.venv-build\Scripts\pip install ".[dev]"
& .\.venv-build\Scripts\pytest
& .\.venv-build\Scripts\pyinstaller --clean --noconfirm scripts\community_pulse.spec
Write-Host "Built dist\CommunityPulseAI.exe"
if (Get-Command iscc -ErrorAction SilentlyContinue) {
  iscc scripts\installer.iss
} else { Write-Warning "Inno Setup not found; executable was built, installer skipped." }
