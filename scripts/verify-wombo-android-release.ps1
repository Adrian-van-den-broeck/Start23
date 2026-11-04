param(
    [Parameter(Mandatory = $true)][string]$BuildRoot,
    [string]$SdkRoot = 'C:\Users\Adria\AppData\Local\Android\Sdk'
)
$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$buildAbsolute = [IO.Path]::GetFullPath($BuildRoot)
if ($buildAbsolute.Length -gt 35 -or $buildAbsolute -eq [IO.Path]::GetPathRoot($buildAbsolute)) {
    throw 'Use a new dedicated short directory, never a drive root.'
}
if (Test-Path -LiteralPath $buildAbsolute) { throw 'BuildRoot already exists; preserve it and choose a new directory.' }
if (-not (Test-Path -LiteralPath $SdkRoot)) { throw 'Existing Android SDK not found.' }
$files = @(& git -C $sourceRoot ls-files -co --exclude-standard -- mobile)
if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate candidate mobile sources.' }
New-Item -ItemType Directory -Path $buildAbsolute | Out-Null
Set-Content -LiteralPath (Join-Path $buildAbsolute '.wombo-native-verification') -Value $sourceRoot -Encoding UTF8
$manifest = [ordered]@{ sourceCommit = (& git -C $sourceRoot rev-parse HEAD); files = [ordered]@{} }
foreach ($relative in ($files | Sort-Object -Unique)) {
    if ($relative -notmatch '^mobile/' -or $relative -match '(^|/)\.\.(/|$)|(^|/)node_modules/|(^|/)credentials[^/]*\.json$|(^|/)\.env($|\.(?!example$))') {
        throw "Refusing unexpected source path: $relative"
    }
    $source = Join-Path $sourceRoot $relative
    $target = [IO.Path]::GetFullPath((Join-Path $buildAbsolute $relative))
    if (-not $target.StartsWith($buildAbsolute + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Copy escaped BuildRoot.' }
    New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
    $manifest.files[$relative] = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $buildAbsolute 'source-manifest.json') -Encoding UTF8
$env:ANDROID_HOME = $SdkRoot
$env:CI = '1'
$env:EXPO_NO_TELEMETRY = '1'
$env:EXPO_PUBLIC_API_BASE_URL = 'https://start23-production.up.railway.app'
$env:EXPO_PUBLIC_SUPABASE_URL = 'https://isfumhgqphieoayqahjv.supabase.co'
$env:EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY = 'native-verification-placeholder-not-a-key'
Push-Location (Join-Path $buildAbsolute 'mobile')
try {
    & npm.cmd ci --ignore-scripts --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
    & node node_modules/expo/bin/cli prebuild --platform android --no-install
    if ($LASTEXITCODE -ne 0) { throw 'Android prebuild failed.' }
    Push-Location android
    try {
        & .\gradlew.bat :app:bundleRelease --offline --no-daemon -PreactNativeArchitectures=arm64-v8a
        if ($LASTEXITCODE -ne 0) { throw 'Local Android release compilation failed.' }
    } finally { Pop-Location }
} finally { Pop-Location }
Write-Output 'Local arm64 verification only: placeholder public configuration/default local signing; not a distributable store artifact.'
