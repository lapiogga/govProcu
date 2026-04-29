# setup-git.ps1 (UTF-8 with BOM)
# GovProcu - Git initialization and first push to GitHub
# Usage:
#   cd C:\Users\User\GovProcu
#   powershell -ExecutionPolicy Bypass -File scripts\setup-git.ps1

$ErrorActionPreference = "Stop"

# Force UTF-8 for console and git operations
chcp 65001 > $null
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:LC_ALL = "C.UTF-8"
$env:LANG   = "C.UTF-8"

Write-Host "==> GovProcu Git initialization starting" -ForegroundColor Cyan

# 1. Remove the broken .git folder created by the Cowork mount
if (Test-Path ".git") {
    Write-Host "Removing existing .git folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".git"
}

# 2. Initialize git
git init -b main
git config user.name  "lapiogga"
git config user.email "lapiogga@gmail.com"
git config core.quotepath false
git config i18n.commitencoding utf-8
git config i18n.logoutputencoding utf-8

# 3. Register remote
git remote add origin https://github.com/lapiogga/govProcu.git

# 4. First commit (commit message read from UTF-8 file to avoid encoding issues)
git add -A
git commit -F scripts\.commit-msg.txt

# 5. Push (Windows Credential Manager will prompt for GitHub login)
Write-Host ""
Write-Host "==> Pushing to GitHub (sign in as 'lapiogga' when prompted)" -ForegroundColor Cyan
git push -u origin main

Write-Host ""
Write-Host "[OK] Done. Visit: https://github.com/lapiogga/govProcu" -ForegroundColor Green
