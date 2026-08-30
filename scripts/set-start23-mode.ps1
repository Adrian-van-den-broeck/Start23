param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('local', 'production')]
    [string]$Mode,

    [string]$RailwayPublicUrl = ''
)

. (Join-Path $PSScriptRoot 'start23-common.ps1')

$repositoryRoot = Get-Start23RepositoryRoot
$mobileEnvPath = Join-Path $repositoryRoot 'mobile\.env'

if ($Mode -eq 'local') {
    $apiBaseUrl = 'http://127.0.0.1:8000'
}
else {
    Initialize-Start23RailwayContext
    $apiBaseUrl = Resolve-Start23RailwayPublicUrl -ProvidedUrl $RailwayPublicUrl
    $polarCallback = "$apiBaseUrl/api/v1/integrations/polar/oauth/callback"

    Write-Host '[Start23] Updating the public Polar callback on Railway (without triggering a deploy)...'
    Invoke-Start23Npx -Package $script:Start23RailwayCli -Arguments @(
        'variable', 'set', "START23_POLAR_OAUTH_REDIRECT_URL=$polarCallback",
        '--service', 'start23', '--skip-deploys'
    )
}

Set-Start23DotEnvValue -Path $mobileEnvPath -Name 'EXPO_PUBLIC_API_BASE_URL' -Value $apiBaseUrl
Set-Start23State -Mode $Mode -ApiBaseUrl $apiBaseUrl

Write-Host "[Start23] Active mode: $Mode"
Write-Host "[Start23] Mobile API: $apiBaseUrl"
if ($Mode -eq 'production') {
    Write-Host '[Start23] The backend task will now deploy service start23 to Railway.'
}
else {
    Write-Host '[Start23] The backend task will now run FastAPI locally.'
}
