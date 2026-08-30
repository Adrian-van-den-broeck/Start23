. (Join-Path $PSScriptRoot 'start23-common.ps1')

$repositoryRoot = Get-Start23RepositoryRoot
$state = Get-Start23State
Write-Host "[Start23] Backend target: $($state.mode)"

if ($state.mode -eq 'local') {
    $pythonPath = Join-Path $repositoryRoot 'backend\.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        throw "Missing '$pythonPath'. Create the backend virtual environment first."
    }

    Push-Location (Join-Path $repositoryRoot 'backend')
    try {
        & $pythonPath -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
        if ($LASTEXITCODE -ne 0) {
            throw 'The local FastAPI process exited with an error.'
        }
    }
    finally {
        Pop-Location
    }
    exit 0
}

if ($state.mode -ne 'production') {
    throw "Unsupported Start23 mode '$($state.mode)'."
}

$publicUrl = ConvertTo-Start23PublicUrl -Value $state.apiBaseUrl
Initialize-Start23RailwayContext
Push-Location $repositoryRoot
try {
    Invoke-Start23Npx -Package $script:Start23RailwayCli -Arguments @(
        'up', $repositoryRoot, '--service', 'start23'
    )
}
finally {
    Pop-Location
}

$readyUrl = "$publicUrl/ready"
Write-Host "[Start23] Checking $readyUrl..."
$ready = Invoke-RestMethod -Uri $readyUrl -Method Get -TimeoutSec 20
if ($null -eq $ready -or $ready.status -ne 'ready') {
    throw "Railway deployed, but '$readyUrl' did not return the expected ready status."
}

Write-Host '[Start23] Railway deployment is healthy. Application startup complete.'
