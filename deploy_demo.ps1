param (
    [string]$ServerHost = "107.175.144.245",
    [string]$ServerUser = "root",
    [string]$ServerAppPath = "/opt/ny-tagging-demo"
)

$ErrorActionPreference = "Stop"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   NY TAGGING DEMO — DEPLOY TO VPS" -ForegroundColor Cyan
Write-Host "   Target: https://tagging-sys.peebot.shop" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Push code lên git
Write-Host "[1/3] Day code len Git..." -ForegroundColor Yellow
$hasChanges = git status --porcelain
if ($hasChanges) {
    git add .
    $commitMsg = "deploy: demo update $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $commitMsg
    git push origin main
} else {
    Write-Host "Khong co thay doi git moi." -ForegroundColor Gray
    git push origin main
}

# 2. Copy database.db len server (neu co)
$dbPath = "$PSScriptRoot\backend_v2\database.db"
if (Test-Path $dbPath) {
    Write-Host "[2/3] Upload database.db len server..." -ForegroundColor Yellow
    scp $dbPath "${ServerUser}@${ServerHost}:${ServerAppPath}/backend_v2/database.db"
} else {
    Write-Host "[2/3] Khong tim thay database.db - bo qua upload DB." -ForegroundColor Gray
    Write-Host "      Chay export_to_sqlite.py truoc neu can data moi." -ForegroundColor Gray
}

# 3. SSH vao server, pull va rebuild
Write-Host "[3/3] Rebuild Docker tren VPS..." -ForegroundColor Yellow
$remoteCmd = @"
cd $ServerAppPath && \
git pull origin main && \
docker compose --env-file .env.demo up -d --build && \
echo '=== Containers ===' && \
docker ps --filter name=ny_tagging_demo --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
"@
ssh "${ServerUser}@${ServerHost}" $remoteCmd

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "   DEPLOY THANH CONG!" -ForegroundColor Green
Write-Host "   URL: https://tagging-sys.peebot.shop" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
