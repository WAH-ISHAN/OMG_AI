# ---------------------------------------------------------
# OMG_AI One-Line Installer
# ---------------------------------------------------------

Write-Host "Starting OMG_AI Installation..." -ForegroundColor Cyan

# 1. Setup Directories
$installDir = "$env:USERPROFILE\OMG_AI"
if (!(Test-Path -Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}

# 2. Download Core Python Script from GitHub
$scriptUrl = "https://raw.githubusercontent.com/WAH-ISHAN/OMG_AI/main/omg_ai.py"
$scriptDest = "$installDir\omg_ai.py"
Write-Host "Downloading Core Components..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $scriptUrl -OutFile $scriptDest -UseBasicParsing

# 3. Create the Wrapper Batch File
$batContent = "@echo off`npython `"%~dp0omg_ai.py`" %*"
$batDest = "$installDir\OMG_AI.bat"
Set-Content -Path $batDest -Value $batContent

# 4. Add to System PATH (User Level)
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notmatch [regex]::Escape($installDir)) {
    $newPath = $userPath + ";$installDir"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Added $installDir to System PATH." -ForegroundColor Green
    
    # Also update current session PATH so it works immediately
    $env:Path += ";$installDir"
}

Write-Host "System Integration Complete!" -ForegroundColor Green

# 5. Launch the Setup Wizard automatically
Write-Host "Launching Setup Wizard..." -ForegroundColor Cyan
Set-Location -Path $installDir
& "$installDir\OMG_AI.bat" install
