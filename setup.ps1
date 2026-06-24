# BlinkPipe — One-shot setup script for Windows (PowerShell)
# Run: .\setup.ps1

Write-Host "`n=== BlinkPipe Setup ===" -ForegroundColor Cyan

# 1. Check Docker is running
Write-Host "`n[1/4] Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "  Docker is running." -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Docker Desktop is not running. Please start it and re-run this script." -ForegroundColor Red
    exit 1
}

# 2. Create required local directories
Write-Host "`n[2/4] Creating local directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "logs","plugins","data","docker\metabase\plugins" | Out-Null
Write-Host "  Created: logs/, plugins/, data/, docker/metabase/plugins/" -ForegroundColor Green

# 3. Build and start all containers
Write-Host "`n[3/4] Building Docker images and starting services..." -ForegroundColor Yellow
Write-Host "  This may take 5-10 minutes on first run (image downloads)." -ForegroundColor Gray
docker-compose up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: docker-compose failed. Check output above." -ForegroundColor Red
    exit 1
}

# 4. Wait for services to be ready
Write-Host "`n[4/4] Waiting for services to be healthy..." -ForegroundColor Yellow
$services = @{
    "MinIO"    = "http://localhost:9000/minio/health/live"
    "Airflow"  = "http://localhost:8080/health"
    "Metabase" = "http://localhost:3000/api/health"
}

foreach ($name in $services.Keys) {
    $url = $services[$name]
    $maxWait = 120
    $waited = 0
    Write-Host "  Waiting for $name..." -NoNewline
    while ($waited -lt $maxWait) {
        try {
            $r = Invoke-WebRequest -Uri $url -TimeoutSec 3 -ErrorAction Stop
            if ($r.StatusCode -eq 200) {
                Write-Host " ready!" -ForegroundColor Green
                break
            }
        } catch {}
        Start-Sleep -Seconds 5
        $waited += 5
        Write-Host "." -NoNewline
    }
    if ($waited -ge $maxWait) {
        Write-Host " TIMEOUT (may still be starting)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== BlinkPipe is ready! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Service URLs:" -ForegroundColor White
Write-Host "    MinIO Console  → http://localhost:9001  (minioadmin / minioadmin)" -ForegroundColor Gray
Write-Host "    Airflow UI     → http://localhost:8080  (admin / admin)" -ForegroundColor Gray
Write-Host "    Metabase       → http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Generate data:  docker-compose exec airflow-webserver python /opt/airflow/scripts/generate_orders.py --days 30" -ForegroundColor Gray
Write-Host "    2. Trigger DAG:    Open Airflow UI → blinkpipe_ingestion → Trigger" -ForegroundColor Gray
Write-Host "    3. View data:      Open Metabase → connect to DuckDB at /data/blinkit.db" -ForegroundColor Gray
Write-Host ""
