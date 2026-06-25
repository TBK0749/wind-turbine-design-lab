$ErrorActionPreference = "Stop"

git pull origin main
uv sync
Write-Host "Wind Turbine Design Lab is up to date."
