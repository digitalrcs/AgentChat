$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host ''
Write-Host 'Welcome to AgentChat setup.' -ForegroundColor Cyan
Write-Host 'This creates a private Python environment in this folder. Your chats will stay in the data folder.'
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $pythonArguments = @('-3')
    if (-not $pythonCommand) { $pythonCommand = Get-Command python -ErrorAction SilentlyContinue; $pythonArguments = @() }
    if (-not $pythonCommand) { throw 'Python was not found. Install Python 3.12, 3.13 or 3.14 from https://www.python.org/downloads/windows/ (include the launcher), then run setup again.' }
    & $pythonCommand.Source @pythonArguments -c "import sys; sys.exit(0 if (3,12) <= sys.version_info[:2] < (3,15) else 1)"
    if ($LASTEXITCODE) { throw 'Please install Python 3.12, 3.13 or 3.14 from https://www.python.org/downloads/windows/, then run setup again.' }
    & $pythonCommand.Source @pythonArguments -m venv .venv
    if ($LASTEXITCODE) { throw 'Could not create the Python environment. Extract AgentChat to a writable folder such as Documents, then try again.' }
}
Write-Host 'Installing the required Python components. Internet access is needed for this step.'
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.lock.txt
if ($LASTEXITCODE) { throw 'Component download failed. Check your internet connection and run setup again. Your existing chats were not changed.' }
if (-not (Test-Path 'dist\index.html')) {
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'This is the source-code download. For the easiest installation, download the Windows ZIP from https://github.com/digitalrcs/AgentChat/releases/latest. Developers can install Node.js 24 and rerun setup.' }
    Write-Host 'Building the interface from source...'
    npm.cmd ci
    if ($LASTEXITCODE) { throw 'Interface dependency installation failed. Check internet access and try again.' }
    npm.cmd run build
    if ($LASTEXITCODE) { throw 'Interface build failed. See the messages above, or use the Windows release ZIP.' }
}
Write-Host ''
Write-Host 'Setup complete. Double-click Start-AgentChat.cmd to open the app.' -ForegroundColor Green
