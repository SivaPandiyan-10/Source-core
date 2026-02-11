<#
Run an end-to-end local demo:
 - Starts the embedding microservice in a background process
 - Indexes the sample corpus
 - Runs the C++ CLI (if built)

Usage: PowerShell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
#>

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) { Write-Host "Python not found; install and try again." -ForegroundColor Red; exit 1 }

Write-Host "Starting embedding microservice..."
Start-Process -FilePath python -ArgumentList "-m uvicorn python.embedding_service:app --port 8000" -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host "Indexing sample corpus..."
python python/index_corpus.py --db personal_ai.db --dir data/sample_docs --endpoint http://127.0.0.1:8000/embed

Write-Host "Running CLI (if built):"
if (Test-Path build\Release\personal_ai.exe) {
    Start-Process -NoNewWindow -FilePath build\Release\personal_ai.exe -Wait
} elseif (Test-Path build\personal_ai.exe) {
    Start-Process -NoNewWindow -FilePath build\personal_ai.exe -Wait
} else {
    Write-Host "Binary not found. Build with CMake first." -ForegroundColor Yellow
}
