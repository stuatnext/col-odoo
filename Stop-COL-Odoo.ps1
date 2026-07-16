$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker was not found on this machine." -ForegroundColor Yellow
    exit 1
}

docker compose down
Write-Host "COL Odoo Platform stopped." -ForegroundColor Green
