<#
Windows setup helper for Personal AI Assistant.
Checks for common dependencies and prints install commands.
Run as: PowerShell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
#>

Write-Host "Checking environment..."

function Check-Command($cmd, $display) {
    $p = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($null -eq $p) { Write-Host "$display: MISSING" -ForegroundColor Yellow; return $false }
    else { Write-Host "$display: present" -ForegroundColor Green; return $true }
}

$cmake = Check-Command -cmd cmake -display "CMake"
$python = Check-Command -cmd python -display "Python"
$pip = Check-Command -cmd pip -display "pip"

Write-Host "If tools are missing, use one of the following options to install:"
Write-Host "- Install Chocolatey (https://chocolatey.org) and then run:" -ForegroundColor Cyan
Write-Host "  choco install -y cmake portablepython3 python pip openssl libsodium" -ForegroundColor Gray
Write-Host "- Or install Visual Studio (Desktop development with C++) and CMake via installer." -ForegroundColor Cyan

Write-Host "Next steps (manual):" -ForegroundColor Green
Write-Host "1) Ensure libsqlite3, libcurl, libsodium dev libraries are installed (via choco or VS components)." -ForegroundColor Gray
Write-Host "2) Install Python requirements: python -m pip install -r python/requirements.txt" -ForegroundColor Gray
Write-Host "3) Build the project: mkdir build; cmake -S . -B build; cmake --build build --config Release" -ForegroundColor Gray
Write-Host "4) (Optional) Start embedding service: uvicorn python.embedding_service:app --port 8000 --reload" -ForegroundColor Gray

Write-Host "Script finished. Review any missing requirements above." -ForegroundColor Green
