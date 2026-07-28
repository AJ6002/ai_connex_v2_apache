# Ensure local mount directories exist
New-Item -ItemType Directory -Force -Path ".\config"
New-Item -ItemType Directory -Force -Path ".\logs"
New-Item -ItemType Directory -Force -Path ".\certs"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Logging into registry.sorbotics.com..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Execute docker login with credentials
echo "SSaa1092p@sorba" | docker login registry.sorbotics.com --username "MITU22BTCS0093@students.mituniversity.edu.in" --password-stdin

if ($LASTEXITCODE -eq 0) {
    Write-Host "Authentication successful. Starting SORBA SDE..." -ForegroundColor Green
    docker-compose up -d
    Write-Host "SORBA SDE is running. Open http://localhost:8080 in your browser to begin." -ForegroundColor Green
} else {
    Write-Host "Authentication failed. Please check your credentials and try again." -ForegroundColor Red
}
