# 1. Define Paths
$ADS_PATH = 'C:\Program Files\Keysight\ADS2025_Update2\tools\python'
$ADS_PYTHON = Join-Path $ADS_PATH 'python.exe'
$WHEEL_DIR = Join-Path $ADS_PATH 'wheelhouse'
$VENV_NAME = "ads_venv"

Write-Host "--- Starting ADS Python Environment Setup ---" -ForegroundColor Cyan

# 2. Environment Check
if (-not (Test-Path $ADS_PYTHON)) {
    Write-Host "ERROR: ADS Python not found at: $ADS_PYTHON" -ForegroundColor Red
    return
}

# 3. Create Virtual Environment
Write-Host "Creating virtual environment [$VENV_NAME]..." -ForegroundColor Yellow
Start-Process -FilePath $ADS_PYTHON -ArgumentList "-m venv $VENV_NAME" -Wait

# 4. Install ADS Libraries (Individual File Processing)
Write-Host "Installing compatible wheels from wheelhouse directory..." -ForegroundColor Yellow
$LOCAL_PIP = Join-Path (Get-Location) "$VENV_NAME\Scripts\python.exe"

# Get all wheel files
$wheels = Get-ChildItem -Path $WHEEL_DIR -Filter *.whl

Push-Location $WHEEL_DIR
foreach ($wheel in $wheels) {
    Write-Host "Attempting to install: $($wheel.Name)..." -NoNewline
    
    # 修正点：显式使用 -m pip 来确保正确调用 pip 模块
    $process = Start-Process -FilePath $LOCAL_PIP -ArgumentList "-m pip install `"$($wheel.FullName)`" --find-links . --no-index" -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host " [SUCCESS]" -ForegroundColor Green
    } else {
        Write-Host " [SKIPPED] (Version mismatch or other error)" -ForegroundColor Gray
    }
}
Pop-Location

# 5. Verification
Write-Host "`n--- Setup Complete! ---" -ForegroundColor Green
Write-Host "To activate this environment, run:"
Write-Host ".\$VENV_NAME\Scripts\activate" -ForegroundColor White

Write-Host "`nInstalled Packages List:"
& $LOCAL_PIP -m pip list