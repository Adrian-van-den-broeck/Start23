Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:Start23RailwayCli = '@railway/cli@5.45.10'
$script:Start23EasCli = 'eas-cli@23.2.0'
$script:Start23SupabaseCli = 'supabase@2.116.0'

function Get-Start23RepositoryRoot {
    return Split-Path -Parent $PSScriptRoot
}

function Invoke-Start23Npx {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Package,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [switch]$CaptureOutput
    )

    if ($CaptureOutput) {
        $output = & npx.cmd --yes $Package @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed: npx $Package $($Arguments -join ' ')"
        }
        return $output -join [Environment]::NewLine
    }

    & npx.cmd --yes $Package @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: npx $Package $($Arguments -join ' ')"
    }
}

function Initialize-Start23RailwayContext {
    try {
        Invoke-Start23Npx -Package $script:Start23RailwayCli -Arguments @('whoami') -CaptureOutput | Out-Null
    }
    catch {
        Write-Host '[Start23] Railway login is required. Complete the browser login to continue...'
        Invoke-Start23Npx -Package $script:Start23RailwayCli -Arguments @('login')
    }

    try {
        Invoke-Start23Npx -Package $script:Start23RailwayCli -Arguments @('status', '--json') -CaptureOutput | Out-Null
    }
    catch {
        Write-Host '[Start23] Link this directory to the existing Railway project and production environment...'
        Invoke-Start23Npx -Package $script:Start23RailwayCli -Arguments @(
            'link', '--service', 'start23'
        )
    }
}

function ConvertTo-Start23PublicUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $candidate = $Value.Trim().TrimEnd('/')
    if (-not $candidate.Contains('://')) {
        $candidate = "https://$candidate"
    }

    $uri = $null
    if (-not [Uri]::TryCreate($candidate, [UriKind]::Absolute, [ref]$uri)) {
        throw "'$Value' is not a valid public URL."
    }
    if ($uri.Scheme -ne 'https') {
        throw 'The production backend URL must use HTTPS.'
    }

    $hostName = $uri.DnsSafeHost.ToLowerInvariant()
    $blockedHosts = @('localhost', '127.0.0.1', '::1', 'start23.railway.internal')
    if ($blockedHosts -contains $hostName -or $hostName.EndsWith('.railway.internal')) {
        throw "'$hostName' is private and cannot be reached by the mobile app. Generate a Railway public domain."
    }
    if (-not $hostName.Contains('.')) {
        throw "'$hostName' is not a public hostname."
    }

    return "https://$($uri.Authority)"
}

function Get-Start23ObjectStrings {
    param([AllowNull()][object]$InputObject)

    if ($null -eq $InputObject) {
        return
    }
    if ($InputObject -is [string]) {
        Write-Output $InputObject
        return
    }
    if ($InputObject -is [System.Collections.IDictionary]) {
        foreach ($value in $InputObject.Values) {
            Get-Start23ObjectStrings -InputObject $value
        }
        return
    }
    if ($InputObject -is [System.Collections.IEnumerable]) {
        foreach ($value in $InputObject) {
            Get-Start23ObjectStrings -InputObject $value
        }
        return
    }
    foreach ($property in $InputObject.PSObject.Properties) {
        Get-Start23ObjectStrings -InputObject $property.Value
    }
}

function Get-Start23PublicUrlFromJson {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Json
    )

    $data = $Json | ConvertFrom-Json
    $candidates = @(Get-Start23ObjectStrings -InputObject $data)
    $orderedCandidates = @(
        $candidates | Where-Object { $_ -match '\.up\.railway\.app(?:/|$)' }
        $candidates | Where-Object { $_ -notmatch '\.up\.railway\.app(?:/|$)' }
    )

    foreach ($candidate in $orderedCandidates) {
        try {
            return ConvertTo-Start23PublicUrl -Value $candidate
        }
        catch {
            continue
        }
    }
    return $null
}

function Get-Start23StatePath {
    return Join-Path (Get-Start23RepositoryRoot) '.runtime\start23-mode.json'
}

function Get-Start23State {
    $statePath = Get-Start23StatePath
    if (-not (Test-Path -LiteralPath $statePath)) {
        return [pscustomobject]@{
            mode = 'local'
            apiBaseUrl = 'http://127.0.0.1:8000'
            railwayService = 'start23'
        }
    }
    return Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
}

function Set-Start23State {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('local', 'production')]
        [string]$Mode,

        [Parameter(Mandatory = $true)]
        [string]$ApiBaseUrl
    )

    $statePath = Get-Start23StatePath
    $stateDirectory = Split-Path -Parent $statePath
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
    $state = [ordered]@{
        mode = $Mode
        apiBaseUrl = $ApiBaseUrl
        railwayService = 'start23'
        updatedAt = [DateTimeOffset]::UtcNow.ToString('O')
    }
    $json = $state | ConvertTo-Json
    [IO.File]::WriteAllText($statePath, "$json`n", [Text.UTF8Encoding]::new($false))
}

function Get-Start23DotEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    $escapedName = [Regex]::Escape($Name)
    $line = Get-Content -LiteralPath $Path | Where-Object { $_ -match "^$escapedName=" } | Select-Object -Last 1
    if ($null -eq $line) {
        return $null
    }
    return ($line -replace "^$escapedName=", '').Trim().Trim('"').Trim("'")
}

function Set-Start23DotEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing '$Path'. Copy mobile/.env.example to mobile/.env and configure the public Supabase values first."
    }

    $content = Get-Content -LiteralPath $Path -Raw
    $escapedName = [Regex]::Escape($Name)
    $replacement = "$Name=$Value"
    if ($content -match "(?m)^$escapedName=.*$") {
        $content = [Regex]::Replace($content, "(?m)^$escapedName=.*$", $replacement)
    }
    else {
        if ($content.Length -gt 0 -and -not $content.EndsWith("`n")) {
            $content += "`n"
        }
        $content += "$replacement`n"
    }
    [IO.File]::WriteAllText($Path, $content, [Text.UTF8Encoding]::new($false))
}

function Resolve-Start23RailwayPublicUrl {
    param([string]$ProvidedUrl)

    if (-not [string]::IsNullOrWhiteSpace($ProvidedUrl)) {
        return ConvertTo-Start23PublicUrl -Value $ProvidedUrl
    }
    if (-not [string]::IsNullOrWhiteSpace($env:START23_RAILWAY_PUBLIC_URL)) {
        return ConvertTo-Start23PublicUrl -Value $env:START23_RAILWAY_PUBLIC_URL
    }

    $state = Get-Start23State
    if ($state.mode -eq 'production' -and -not [string]::IsNullOrWhiteSpace($state.apiBaseUrl)) {
        return ConvertTo-Start23PublicUrl -Value $state.apiBaseUrl
    }

    Write-Host '[Start23] Looking up the public Railway domain for service start23...'
    $domainJson = Invoke-Start23Npx -Package $script:Start23RailwayCli -Arguments @(
        'domain', 'list', '--service', 'start23', '--json'
    ) -CaptureOutput
    $publicUrl = Get-Start23PublicUrlFromJson -Json $domainJson
    if ($null -ne $publicUrl) {
        return $publicUrl
    }

    Write-Host '[Start23] No public domain exists yet; generating a Railway domain...'
    $domainJson = Invoke-Start23Npx -Package $script:Start23RailwayCli -Arguments @(
        'domain', '--service', 'start23', '--json'
    ) -CaptureOutput
    $publicUrl = Get-Start23PublicUrlFromJson -Json $domainJson
    if ($null -eq $publicUrl) {
        throw 'Railway did not return a public domain. Generate one under Public Networking and run the task again.'
    }
    return $publicUrl
}
