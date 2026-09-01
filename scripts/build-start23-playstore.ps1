param(
    [string]$BuildId
)

. (Join-Path $PSScriptRoot 'start23-common.ps1')

$repositoryRoot = Get-Start23RepositoryRoot
$mobileRoot = Join-Path $repositoryRoot 'mobile'
$mobileEnvPath = Join-Path $mobileRoot '.env'
$state = Get-Start23State
$buildProfile = 'wombo'
$expectedPackage = 'com.adrivdbs.wombo'

if ($state.mode -ne 'production') {
    throw 'Switch Wombo to production mode before creating a Play Store build.'
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
    if ([string]::IsNullOrWhiteSpace($BuildId)) {
        Write-Host '[Wombo] Syncing public mobile configuration to the EAS production environment...'
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

        Write-Host "[Wombo] Building $expectedPackage for Google Play. EAS will increment versionCode remotely..."
        $buildRequestJson = Invoke-Start23Npx -Package $script:Start23EasCli -Arguments @(
            'build', '--platform', 'android', '--profile', $buildProfile,
            '--wait', '--json', '--non-interactive'
        ) -CaptureOutput
        $buildRequests = @($buildRequestJson | ConvertFrom-Json)
        if ($buildRequests.Count -ne 1 -or [string]::IsNullOrWhiteSpace($buildRequests[0].id)) {
            throw 'EAS did not return exactly one Android build ID.'
        }
        $BuildId = [string]$buildRequests[0].id
    }
    else {
        Write-Host "[Wombo] Resuming completed EAS build $BuildId without creating a new versionCode..."
    }

    $buildJson = Invoke-Start23Npx -Package $script:Start23EasCli -Arguments @(
        'build:view', $BuildId, '--json'
    ) -CaptureOutput
    $latestBuild = $buildJson | ConvertFrom-Json
    if ($latestBuild.status -ne 'FINISHED') {
        throw "EAS build '$BuildId' has status '$($latestBuild.status)' instead of 'FINISHED'."
    }
    $actualPackage = if ($latestBuild.PSObject.Properties.Name -contains 'appIdentifier') {
        [string]$latestBuild.appIdentifier
    }
    elseif ($latestBuild.PSObject.Properties.Name -contains 'applicationIdentifier') {
        [string]$latestBuild.applicationIdentifier
    }
    else {
        $null
    }
    if ([string]::IsNullOrWhiteSpace($actualPackage)) {
        throw "EAS build '$BuildId' did not return an Android package identifier."
    }
    if ($actualPackage -cne $expectedPackage) {
        throw "EAS returned package '$actualPackage' instead of '$expectedPackage'."
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
    $outputPath = Join-Path $outputDirectory "wombo-playstore-$versionCode.aab"
    Invoke-WebRequest -Uri $artifactUrl -OutFile $outputPath -UseBasicParsing

    Write-Host "[Wombo] Play Store bundle downloaded to: $outputPath"
    Write-Host "[Wombo] Android package: $expectedPackage"
}
finally {
    Pop-Location
}
