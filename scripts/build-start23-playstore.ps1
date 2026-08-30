param(
    [ValidateSet('production', 'wombo')]
    [string]$BuildProfile = 'production'
)

. (Join-Path $PSScriptRoot 'start23-common.ps1')

$repositoryRoot = Get-Start23RepositoryRoot
$mobileRoot = Join-Path $repositoryRoot 'mobile'
$mobileEnvPath = Join-Path $mobileRoot '.env'
$state = Get-Start23State
$expectedPackage = if ($BuildProfile -eq 'wombo') {
    'com.adrivdbs.wombo'
}
else {
    'com.adrivdbs.start23'
}

if ($state.mode -ne 'production') {
    throw 'Switch Start23 to production mode before creating a Play Store build.'
}

$apiBaseUrl = ConvertTo-Start23PublicUrl -Value $state.apiBaseUrl
$supabaseUrl = Get-Start23DotEnvValue -Path $mobileEnvPath -Name 'EXPO_PUBLIC_SUPABASE_URL'
$supabasePublishableKey = Get-Start23DotEnvValue -Path $mobileEnvPath -Name 'EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY'

if ([string]::IsNullOrWhiteSpace($supabaseUrl)) {
    throw 'EXPO_PUBLIC_SUPABASE_URL is missing from mobile/.env.'
}
if ([string]::IsNullOrWhiteSpace($supabasePublishableKey) -or $supabasePublishableKey -match 'replace_with') {
    throw 'Configure a Supabase publishable key in mobile/.env before building.'
}

Push-Location $mobileRoot
try {
    Write-Host '[Start23] Syncing public mobile configuration to the EAS production environment...'
    $publicVariables = [ordered]@{
        EXPO_PUBLIC_API_BASE_URL = $apiBaseUrl
        EXPO_PUBLIC_SUPABASE_URL = $supabaseUrl
        EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY = $supabasePublishableKey
    }
    foreach ($entry in $publicVariables.GetEnumerator()) {
        Invoke-Start23Npx -Package $script:Start23EasCli -Arguments @(
            'env:set', 'production', '--name', $entry.Key, '--value', $entry.Value,
            '--visibility', 'plaintext', '--scope', 'project', '--non-interactive'
        )
    }

    Write-Host "[Start23] Building $expectedPackage for Google Play. EAS will increment versionCode remotely..."
    Invoke-Start23Npx -Package $script:Start23EasCli -Arguments @(
        'build', '--platform', 'android', '--profile', $BuildProfile, '--wait'
    )

    $latestBuildJson = Invoke-Start23Npx -Package $script:Start23EasCli -Arguments @(
        'build:list', '--platform', 'android', '--build-profile', $BuildProfile,
        '--status', 'finished', '--limit', '1', '--json', '--non-interactive'
    ) -CaptureOutput
    $latestBuild = @($latestBuildJson | ConvertFrom-Json)[0]
    if (
        $latestBuild.PSObject.Properties.Name -contains 'applicationIdentifier' -and
        $latestBuild.applicationIdentifier -ne $expectedPackage
    ) {
        throw "EAS returned package '$($latestBuild.applicationIdentifier)' instead of '$expectedPackage'."
    }
    $artifactUrl = $null
    if ($null -ne $latestBuild.artifacts) {
        $artifactProperties = $latestBuild.artifacts.PSObject.Properties
        if ($artifactProperties.Name -contains 'applicationArchiveUrl') {
            $artifactUrl = $latestBuild.artifacts.applicationArchiveUrl
        }
        if (
            [string]::IsNullOrWhiteSpace($artifactUrl) -and
            $artifactProperties.Name -contains 'buildUrl'
        ) {
            $artifactUrl = $latestBuild.artifacts.buildUrl
        }
    }
    if ([string]::IsNullOrWhiteSpace($artifactUrl)) {
        throw 'The EAS build succeeded, but no downloadable Android artifact URL was returned.'
    }

    $versionCode = $null
    if ($latestBuild.PSObject.Properties.Name -contains 'appBuildVersion') {
        $versionCode = $latestBuild.appBuildVersion
    }
    if ([string]::IsNullOrWhiteSpace($versionCode)) {
        $versionCode = [DateTimeOffset]::UtcNow.ToString('yyyyMMddHHmmss')
    }
    $outputDirectory = Join-Path $mobileRoot 'dist'
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    $artifactName = if ($BuildProfile -eq 'wombo') { 'start23-wombo' } else { 'start23' }
    $outputPath = Join-Path $outputDirectory "$artifactName-playstore-$versionCode.aab"
    Invoke-WebRequest -Uri $artifactUrl -OutFile $outputPath -UseBasicParsing

    Write-Host "[Start23] Play Store bundle downloaded to: $outputPath"
    Write-Host "[Start23] Android package: $expectedPackage"
}
finally {
    Pop-Location
}
