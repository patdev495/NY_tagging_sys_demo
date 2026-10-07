param (
    [string]$ServerHost = "192.168.209.62",
    [string]$ServerUser = "Admin",
    [string]$ServerAppPath = "D:\projects_production\NY_tagging_sys_new"
)

$ErrorActionPreference = "Stop"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   NY TAGGING SYSTEM - 1-CLICK DEPLOY (SSH)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Build Frontend
Write-Host "[1/4] Dang build Frontend V2..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\frontend_v2"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build frontend that bai!"
    exit $LASTEXITCODE
}

# 2. Sync frontend dist vao backend_v2/static
Write-Host "[2/4] Dong bo dist vao backend_v2/static..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot"
if (Test-Path "$PSScriptRoot\backend_v2\static") {
    Remove-Item -Recurse -Force "$PSScriptRoot\backend_v2\static"
}
Copy-Item -Recurse "$PSScriptRoot\frontend_v2\dist" "$PSScriptRoot\backend_v2\static"

# 3. Commit va push len GitHub
Write-Host "[3/4] Day code len GitHub..." -ForegroundColor Yellow
git add .
$hasChanges = git status --porcelain
if ($hasChanges) {
    $commitMsg = "deploy: auto update $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $commitMsg
    git push origin main
} else {
    Write-Host "Khong co thay doi git moi, tiep tuc cap nhat server..." -ForegroundColor Gray
}

# 4. Gui lenh qua SSH de Server tu update va restart
Write-Host "[4/4] Kich hoat Server cap nhat qua SSH ($ServerUser@$ServerHost)..." -ForegroundColor Yellow
$remoteCommand = "cd /d $ServerAppPath && git reset --hard origin/main && git pull origin main && cd backend_v2 && C:\Users\Admin\.local\bin\uv sync && nssm restart ny-tagging-8002"
ssh "$ServerUser@$ServerHost" $remoteCommand

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "   DEPLOY THANH CONG! Server da chay ban moi nhat." -ForegroundColor Green
Write-Host "   Web URL: http://${ServerHost}:8002" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
