$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Run Setup-AgentChat.ps1 first.' }
if (-not (Test-Path 'dist\index.html')) { throw 'Run npm.cmd run build first.' }
Write-Host 'AgentChat: http://127.0.0.1:8765'
Write-Host 'Keep this window open while using AgentChat. Press Ctrl+C here to stop it.'
try {
    $existing = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/health' -TimeoutSec 2
    if ($existing.status -eq 'ok' -and $existing.service -eq 'agentchat') {
        Write-Host 'AgentChat is already running. Opening it in your browser.'
        Start-Process 'http://127.0.0.1:8765'
        exit 0
    }
} catch { }
& '.\.venv\Scripts\python.exe' 'run.py' 'web' '--open-browser'
if ($LASTEXITCODE) { throw 'AgentChat could not start. Another program may be using port 8765. See the messages above.' }
