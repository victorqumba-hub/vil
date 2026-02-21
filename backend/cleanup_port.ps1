$port = 8000
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1

if ($connection) {
    $pidToKill = $connection.OwningProcess
    $process = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Found process $pidToKill ($($process.ProcessName)) listening on port $port. Terminating..." -ForegroundColor Yellow
        Stop-Process -Id $pidToKill -Force
        Write-Host "Process $pidToKill terminated successfully." -ForegroundColor Green
    }
    else {
        Write-Host "Connection entry found for port $port (PID $pidToKill), but process is already gone." -ForegroundColor Cyan
    }
}
else {
    Write-Host "No process found listening on port $port." -ForegroundColor Cyan
}
