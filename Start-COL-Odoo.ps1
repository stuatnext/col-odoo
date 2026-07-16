$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host ""
Write-Host "COL Odoo Platform" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker was not found on this machine." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Install Docker Desktop first:"
    Write-Host "https://www.docker.com/products/docker-desktop/"
    Write-Host ""
    Write-Host "Then reopen PowerShell in this folder and run:"
    Write-Host ".\Start-COL-Odoo.ps1"
    exit 1
}

Write-Host "Copying import files into the mounted import folder..."
New-Item -ItemType Directory -Force -Path ".\odoo\import" | Out-Null

$catalogCsv = ".\COL Master Catalog (consolidated).csv"
$rightsModel = ".\COL Rights & Avails Model.xlsx"

if (Test-Path $catalogCsv) {
    Copy-Item -LiteralPath $catalogCsv -Destination ".\odoo\import\" -Force
}

if (Test-Path $rightsModel) {
    Copy-Item -LiteralPath $rightsModel -Destination ".\odoo\import\" -Force
}

Write-Host "Starting Odoo and Postgres..."
docker compose up -d

Write-Host ""
Write-Host "Odoo is starting." -ForegroundColor Green
Write-Host "Open: http://localhost:8069"
Write-Host ""
Write-Host "First-time setup:"
Write-Host "1. Create a new database."
Write-Host "2. Master password: col-admin-change-me"
Write-Host "3. Apps > Update Apps List."
Write-Host "4. Install: COL Content Rights & Avails."
Write-Host "5. Install CRM and Project."
Write-Host "6. Install: COL Content Rights - CRM Bridge."
Write-Host "7. Install: COL Sales & Delivery."
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  docker compose logs -f odoo"
Write-Host "  docker compose down"
Write-Host "  docker compose down -v   # deletes local Odoo/Postgres data"
