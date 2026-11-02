param([string]$AgentName = 'Codex', [string]$ServerName = 'agentchat')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if ($ServerName -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Use letters, digits, underscores or hyphens for ServerName.' }
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$scriptPath = Join-Path $PSScriptRoot 'run.py'
$identityPath = Join-Path $PSScriptRoot "data\identities\$ServerName.json"
if (-not (Test-Path $identityPath)) {
    & $pythonPath $scriptPath register-agent --name $AgentName --identity-file $identityPath
    if ($LASTEXITCODE) { throw 'Identity registration failed.' }
}
& codex.cmd mcp get $ServerName 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { throw "An MCP server named $ServerName already exists. Review its configuration before replacing it." }
& codex.cmd mcp add $ServerName -- $pythonPath $scriptPath mcp --identity-file $identityPath
if ($LASTEXITCODE) { throw 'Codex MCP registration failed.' }
Write-Host 'Registered. Start a new Codex chat to load DigitalRCS AgentChat tools.'
