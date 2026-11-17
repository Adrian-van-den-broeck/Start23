param(
    [string]$AvdName = 'Pixel_4_API_35_2',
    [ValidateSet('v1', 'v2')]
    [string]$UiVersion = 'v2',
    [switch]$BuildOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$mobileRoot = Join-Path $repositoryRoot 'mobile'
$runtimeMobileRoot = $mobileRoot

function Resolve-AndroidBuildMobileRoot {
    param([string]$WorkspaceMobileRoot, [string]$RuntimeMobileRoot)
    # A shared APK is safe only while every native input matches. New UI
    # dependencies must be compiled from the UI source, not the older checkout.
    foreach ($nativeInput in @('package.json', 'package-lock.json', 'app.json')) {
        $buildInput = (Get-Content -LiteralPath (Join-Path $WorkspaceMobileRoot $nativeInput) -Raw) -replace '\r\n?', "`n"
        $uiInput = (Get-Content -LiteralPath (Join-Path $RuntimeMobileRoot $nativeInput) -Raw) -replace '\r\n?', "`n"
        if ($buildInput -cne $uiInput) { return $RuntimeMobileRoot }
    }
    return $WorkspaceMobileRoot
}

if (-not $BuildOnly) {
    # The stabilization checkout has no V2 components. Run the existing UI
    # integration source, whose development control can display either version.
    $uiCommit = & git -C $repositoryRoot rev-parse --verify refs/heads/feat/wombo-ui-v2
    if ($LASTEXITCODE -ne 0) { throw 'The local feat/wombo-ui-v2 integration branch is unavailable.' }
    $worktrees = @(& git -C $repositoryRoot worktree list --porcelain)
    if ($LASTEXITCODE -ne 0) { throw 'Could not list local UI worktrees.' }
    $uiRoot = $null
    foreach ($line in $worktrees) {
        if ($line -match '^worktree (.+)$') {
            $candidateRoot = $Matches[1]
            $candidateCommit = & git -C $candidateRoot rev-parse HEAD
            if ($LASTEXITCODE -eq 0 -and $candidateCommit -eq $uiCommit -and
                (Test-Path -LiteralPath (Join-Path $candidateRoot 'mobile\src\ui\UiVersionProvider.tsx'))) {
                $uiRoot = $candidateRoot
                break
            }
        }
    }
    if ($null -eq $uiRoot) {
        throw 'No worktree contains the current feat/wombo-ui-v2 integration commit. Create a local worktree for that branch and install its mobile dependencies first.'
    }
    $runtimeMobileRoot = Join-Path $uiRoot 'mobile'
    if (-not (Test-Path -LiteralPath (Join-Path $runtimeMobileRoot 'node_modules\expo\bin\cli'))) {
        throw "Run npm ci in '$runtimeMobileRoot' before starting the UI comparison."
    }
    # Keep the backend target configured by this workspace's existing tasks.
    # Copy only the three public client values into this process, never secrets.
    . (Join-Path $PSScriptRoot 'start23-common.ps1')
    foreach ($publicName in @('EXPO_PUBLIC_API_BASE_URL', 'EXPO_PUBLIC_SUPABASE_URL', 'EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY')) {
        if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($publicName))) {
            $publicValue = Get-Start23DotEnvValue -Path (Join-Path $mobileRoot '.env') -Name $publicName
            if ([string]::IsNullOrWhiteSpace($publicValue)) { throw "Missing $publicName in mobile/.env." }
            [Environment]::SetEnvironmentVariable($publicName, $publicValue)
        }
    }
    $env:EXPO_PUBLIC_UI_VERSION = $UiVersion
    Write-Host "[Wombo] UI comparison source: $uiRoot ($($uiCommit.Substring(0, 7))); initial UI: $UiVersion"
    Write-Host '[Wombo] Use the UI V1 / UI V2 buttons in the app to switch without signing out.'
}
$buildMobileRoot = Resolve-AndroidBuildMobileRoot -WorkspaceMobileRoot $mobileRoot -RuntimeMobileRoot $runtimeMobileRoot
$buildRoot = Split-Path -Parent $buildMobileRoot
$sdkRoot = $env:ANDROID_HOME
if ([string]::IsNullOrWhiteSpace($sdkRoot)) {
    $sdkRoot = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
}
$adb = Join-Path $sdkRoot 'platform-tools\adb.exe'
$emulator = Join-Path $sdkRoot 'emulator\emulator.exe'
$workspaceExpo = Join-Path $mobileRoot 'node_modules\expo\bin\cli'
$expo = Join-Path $buildMobileRoot 'node_modules\expo\bin\cli'
foreach ($tool in @($adb, $emulator, $expo)) {
    if (-not (Test-Path -LiteralPath $tool)) {
        throw "Missing '$tool'. Install the Android SDK and run npm ci in mobile first."
    }
}
$env:ANDROID_HOME = $sdkRoot
$env:ANDROID_SDK_ROOT = $sdkRoot
$env:ANDROID_USER_HOME = Join-Path $env:USERPROFILE '.android'
$env:NODE_ENV = 'development'

function Invoke-AndroidAdbProcess {
    param([string[]]$AdbArguments, [int]$TimeoutMilliseconds = 20000)
    $client = [Diagnostics.Process]::new()
    try {
        $client.StartInfo.FileName = $adb
        # Quote for Windows CreateProcess, without passing arguments to a shell.
        $client.StartInfo.Arguments = (@($AdbArguments | ForEach-Object {
            '"' + ($_ -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
        }) -join ' ')
        $client.StartInfo.UseShellExecute = $false
        $client.StartInfo.CreateNoWindow = $true
        $client.StartInfo.RedirectStandardOutput = $true
        $client.StartInfo.RedirectStandardError = $true
        if (-not $client.Start()) { throw 'Could not start the Android SDK adb client.' }
        $stdout = $client.StandardOutput.ReadToEndAsync()
        $stderr = $client.StandardError.ReadToEndAsync()
        if (-not $client.WaitForExit($TimeoutMilliseconds)) {
            if (-not $client.HasExited) { $client.Kill() }
            $client.WaitForExit(5000) | Out-Null
            return [pscustomobject]@{ TimedOut = $true; ExitCode = -1; Output = ''; ErrorOutput = '' }
        }
        # Drain both redirected streams; never write Android output to logs here.
        $output = $stdout.GetAwaiter().GetResult()
        $errorOutput = $stderr.GetAwaiter().GetResult()
        return [pscustomobject]@{ TimedOut = $false; ExitCode = $client.ExitCode; Output = $output; ErrorOutput = $errorOutput }
    }
    finally { $client.Dispose() }
}

function Restart-AndroidAdbServer {
    # A hung daemon may not respond to 'adb kill-server'. Stop only this SDK's
    # verified default daemon; emulator and application data remain intact.
    $servers = @(Get-CimInstance Win32_Process -Filter "Name = 'adb.exe'" | Where-Object {
        $_.ExecutablePath -ieq $adb -and $_.CommandLine -match '-L\s+tcp:5037\s+fork-server\s+server(?:\s|$)'
    })
    foreach ($server in $servers) {
        $current = Get-CimInstance Win32_Process -Filter "ProcessId = $($server.ProcessId)" -ErrorAction SilentlyContinue
        if ($null -ne $current -and $current.CreationDate -eq $server.CreationDate -and
            $current.ExecutablePath -ieq $adb -and $current.CommandLine -eq $server.CommandLine) {
            Stop-Process -Id $current.ProcessId -ErrorAction SilentlyContinue
        }
    }
    for ($attempt = 0; $attempt -lt 2; $attempt++) {
        $restart = Invoke-AndroidAdbProcess -AdbArguments @('start-server') -TimeoutMilliseconds 10000
        if (-not $restart.TimedOut -and $restart.ExitCode -eq 0) { return }
        # Another SDK client may have started the daemon at the same time.
        $health = Invoke-AndroidAdbProcess -AdbArguments @('devices') -TimeoutMilliseconds 5000
        if (-not $health.TimedOut -and $health.ExitCode -eq 0) { return }
    }
    throw 'Could not recover the Android SDK adb server.'
}

function Invoke-AndroidAdb {
    param([string[]]$AdbArguments)
    for ($attempt = 0; $attempt -lt 2; $attempt++) {
        $result = Invoke-AndroidAdbProcess -AdbArguments $AdbArguments
        if ($result.TimedOut) {
            if ($attempt -eq 1) { throw 'ADB did not respond after automatic recovery. Restart the emulator and try again.' }
            Write-Host '[Wombo] Android connection timed out; recovering the SDK adb server and retrying...'
            Restart-AndroidAdbServer
            if ($AdbArguments.Count -ge 2 -and $AdbArguments[0] -eq '-s') {
                $reconnect = Invoke-AndroidAdbProcess -AdbArguments @('-s', $AdbArguments[1], 'wait-for-device') -TimeoutMilliseconds 10000
                if ($reconnect.TimedOut -or $reconnect.ExitCode -ne 0) { throw 'The emulator did not reconnect after ADB recovery.' }
            }
            continue
        }
        if ($result.ExitCode -ne 0) { throw "adb $($AdbArguments -join ' ') failed." }
        # The emulator console can emit CR-CR-LF; normalize like PowerShell's
        # native output reader so an already-running AVD is matched exactly.
        return @($result.Output -split '\r?\n' | ForEach-Object { $_.TrimEnd("`r") })
    }
}

function Get-AndroidPortListeners {
    param([int]$Port)
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
}

function Get-AndroidServerProcess {
    param([int]$ProcessId)
    Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
}

function Test-AndroidMetroProcess {
    param($ServerProcess, [string[]]$ExpoCliPaths)
    if ($null -eq $ServerProcess -or $ServerProcess.Name -ine 'node.exe' -or
        [string]::IsNullOrWhiteSpace($ServerProcess.CommandLine)) { return $false }
    $command = $ServerProcess.CommandLine.Replace('/', '\')
    foreach ($cliPath in $ExpoCliPaths) {
        $pattern = '(?:^|\s|")' + [Regex]::Escape($cliPath.Replace('/', '\')) + '(?:\s|"|$)'
        if ($command -match $pattern) { return $true }
    }
    return $false
}

function Stop-AndroidMetroProcess {
    param($ServerProcess, [string[]]$ExpoCliPaths)
    # Recheck process identity: the PID could have been reused after inspection.
    $current = Get-AndroidServerProcess -ProcessId $ServerProcess.ProcessId
    if ($null -ne $current -and $current.CreationDate -eq $ServerProcess.CreationDate -and
        (Test-AndroidMetroProcess -ServerProcess $current -ExpoCliPaths $ExpoCliPaths)) {
        # A concurrent stop may already have ended it. Port probing below
        # decides whether to reuse this port or move to another free one.
        Stop-Process -Id $current.ProcessId -ErrorAction SilentlyContinue
    }
}

function Resolve-AndroidMetroPort {
    param([string[]]$ExpoCliPaths)
    foreach ($candidatePort in 8081..8099) {
        $listeners = @(Get-AndroidPortListeners -Port $candidatePort)
        if ($listeners.Count -gt 0) {
            $ownerIds = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
            $owners = @($ownerIds | ForEach-Object { Get-AndroidServerProcess -ProcessId $_ })
            $knownMetro = $owners.Count -eq $ownerIds.Count
            foreach ($owner in $owners) {
                if (-not (Test-AndroidMetroProcess -ServerProcess $owner -ExpoCliPaths $ExpoCliPaths)) {
                    $knownMetro = $false
                }
            }
            if ($knownMetro) {
                Write-Host "[Wombo] Restarting this workspace's Metro server on port $candidatePort..."
                foreach ($owner in $owners) { Stop-AndroidMetroProcess -ServerProcess $owner -ExpoCliPaths $ExpoCliPaths }
                for ($attempt = 0; $attempt -lt 50; $attempt++) {
                    $listeners = @(Get-AndroidPortListeners -Port $candidatePort)
                    if ($listeners.Count -eq 0) { break }
                    Start-Sleep -Milliseconds 200
                }
            }
        }
        if ($listeners.Count -eq 0) {
            if ($candidatePort -ne 8081) { Write-Host "[Wombo] Using free Metro port $candidatePort." }
            return $candidatePort
        }
    }
    throw 'No Metro port is available between 8081 and 8099.'
}

function Get-AndroidAvailableBytes {
    $storage = @(Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'shell', 'df', '-k', '/data'))
    foreach ($line in $storage) {
        if ($line -match '^\S+\s+\d+\s+\d+\s+(\d+)\s+\d+%\s+/data(?:/\S*)?\s*$') {
            return [long]$Matches[1] * 1KB
        }
    }
    throw "Could not determine internal storage on emulator '$AvdName': $($storage -join ' ')"
}

function Assert-AndroidInstallSpace {
    param([long]$ApkBytes = 0)

    # Leave room for Android's low-storage reserve, staging and extracted files.
    # This is a development-install budget, not Android's exact size calculation.
    $requiredBytes = [long][Math]::Max(512MB, 3 * $ApkBytes + 256MB)
    $availableBytes = Get-AndroidAvailableBytes
    if ($availableBytes -lt $requiredBytes) {
        Write-Host "[Wombo] Emulator storage is low; reclaiming disposable caches and the stale debug installer..."
        Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'shell', 'pm', 'trim-caches', "$requiredBytes", 'internal') | Out-Null
        Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'shell', 'rm', '-f', '/data/local/tmp/app-debug.apk') | Out-Null
        $availableBytes = Get-AndroidAvailableBytes
    }
    $availableMiB = [Math]::Floor($availableBytes / 1MB)
    $requiredMiB = [Math]::Ceiling($requiredBytes / 1MB)
    if ($availableBytes -lt $requiredBytes) {
        throw "Emulator '$AvdName' has only $availableMiB MiB free in /data; this development install needs a budget of $requiredMiB MiB. Cache cleanup was insufficient. Run the task with another AVD (default: Pixel_4_API_35_2), or free internal storage in Android Settings > Storage on this AVD. Installed apps and app data have been preserved."
    }
    Write-Host "[Wombo] Emulator internal storage: $availableMiB MiB free."
}

$architecture = 'x86_64'
$serial = $null
$metroPort = 8081
if (-not $BuildOnly) {
    $runtimeExpo = Join-Path $runtimeMobileRoot 'node_modules\expo\bin\cli'
    $metroPort = Resolve-AndroidMetroPort -ExpoCliPaths @($workspaceExpo, $expo, $runtimeExpo)
    $devices = @(Invoke-AndroidAdb -AdbArguments @('devices') | ForEach-Object {
        if ($_ -match '^(emulator-\d+)\s+device$') { $Matches[1] }
    })
    foreach ($device in $devices) {
        $name = @(Invoke-AndroidAdb -AdbArguments @('-s', $device, 'emu', 'avd', 'name'))
        if ($name -contains $AvdName) { $serial = $device; break }
    }
    if ($null -eq $serial) {
        $avds = @(& $emulator -list-avds)
        if ($LASTEXITCODE -ne 0 -or $avds -notcontains $AvdName) {
            throw "Android emulator '$AvdName' is unavailable. Available AVDs: $($avds -join ', ')."
        }
        Write-Host "[Wombo] Starting emulator: $AvdName"
        Start-Process -FilePath $emulator -ArgumentList @('-avd', $AvdName, '-no-snapshot-load') -WindowStyle Hidden | Out-Null
    }

    Write-Host '[Wombo] Waiting for Android to finish booting...'
    $deadline = [DateTime]::UtcNow.AddMinutes(3)
    $booted = $false
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($null -eq $serial) {
            foreach ($line in @(Invoke-AndroidAdb -AdbArguments @('devices'))) {
                if ($line -match '^(emulator-\d+)\s+device$') {
                    $candidate = $Matches[1]
                    $name = @(Invoke-AndroidAdb -AdbArguments @('-s', $candidate, 'emu', 'avd', 'name'))
                    if ($name -contains $AvdName) { $serial = $candidate; break }
                }
            }
        }
        if ($null -ne $serial) {
            $bootStatus = Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'shell', 'getprop', 'sys.boot_completed')
            if ("$bootStatus".Trim() -eq '1') { $booted = $true; break }
        }
        Start-Sleep -Seconds 2
    }
    if (-not $booted) { throw 'The Android emulator did not finish booting within three minutes.' }
    $architecture = "$(Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'shell', 'getprop', 'ro.product.cpu.abi'))".Trim()
    if ($architecture -notin @('x86', 'x86_64', 'arm64-v8a', 'armeabi-v7a')) {
        throw "Unsupported emulator architecture '$architecture'."
    }
    # Fail before an expensive build or Metro startup when the AVD is full.
    Assert-AndroidInstallSpace
    foreach ($port in @($metroPort, 8000)) {
        Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'reverse', "tcp:$port", "tcp:$port") | Out-Null
    }
}

# SUBST exposes the selected native source under a short path without moving it.
# Use a free drive and release only the mapping created by this invocation.
$buildDrive = $null
foreach ($letter in 90..68) {
    $candidateDrive = "$([char]$letter):"
    if (-not (Test-Path "$candidateDrive\") -and
        $null -eq (Get-PSDrive -Name ([string][char]$letter) -ErrorAction SilentlyContinue)) {
        & subst.exe $candidateDrive $buildRoot
        if ($LASTEXITCODE -eq 0) { $buildDrive = $candidateDrive; break }
    }
}
if ($null -eq $buildDrive) { throw 'No free drive letter is available for the short Android build path.' }

try {
    $shortMobileRoot = "$buildDrive\mobile"
    Push-Location $shortMobileRoot
    try {
        if (-not (Test-Path -LiteralPath 'android\gradlew.bat')) {
            & node $expo prebuild --platform android --no-install
            if ($LASTEXITCODE -ne 0) { throw 'Expo Android prebuild failed.' }
        }
        Write-Host "[Wombo] Building Android ($architecture) through $shortMobileRoot..."
        & '.\android\gradlew.bat' -p android app:assembleDebug -x lint -x test --build-cache `
            --init-script (Join-Path $PSScriptRoot 'android-short-paths.gradle') `
            "-Dstart23.projectRoot=$buildRoot" `
            "-Dstart23.nativeRoot=$buildDrive/.runtime/android-native" `
            "-PreactNativeDevServerPort=$metroPort" "-PreactNativeArchitectures=$architecture"
        if ($LASTEXITCODE -ne 0) { throw 'Android development build failed; see the Gradle output above.' }
    }
    finally { Pop-Location }

    $apk = Join-Path $buildMobileRoot 'android\app\build\outputs\apk\debug\app-debug.apk'
    if (-not (Test-Path -LiteralPath $apk)) { throw "Gradle did not produce '$apk'." }
    if ($BuildOnly) {
        Write-Host "[Wombo] Development APK built: $apk"
    }
    else {
        Assert-AndroidInstallSpace -ApkBytes (Get-Item -LiteralPath $apk).Length
        $runtimeAndroidRoot = Join-Path $runtimeMobileRoot 'android'
        if ($runtimeMobileRoot -ne $mobileRoot -and -not (Test-Path -LiteralPath $runtimeAndroidRoot)) {
            # Expo resolves native launch metadata even with --binary. Reuse the
            # checked native project instead of prebuilding and editing UI files.
            New-Item -ItemType Junction -Path $runtimeAndroidRoot -Target (Join-Path $buildMobileRoot 'android') | Out-Null
        }
        Write-Host "[Wombo] Installing development app on $serial..."
        $deviceName = @(Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'emu', 'avd', 'name'))[0].Trim()
        Push-Location $runtimeMobileRoot
        try {
            $env:REACT_NATIVE_PACKAGER_HOSTNAME = '127.0.0.1'
            # Start at the app's root route instead of resuming an old native view.
            # Force-stop keeps the stored login and all application data intact.
            $appConfig = Get-Content -LiteralPath (Join-Path $buildMobileRoot 'app.json') -Raw | ConvertFrom-Json
            Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'shell', 'am', 'force-stop', $appConfig.expo.android.package) | Out-Null
            Write-Host "[Wombo] Starting Metro and opening the app's start screen on localhost:$metroPort..."
            & node $runtimeExpo run:android --binary $apk --device $deviceName --port $metroPort --no-install
            if ($LASTEXITCODE -ne 0) { throw 'Expo failed to start the Android app.' }
        }
        finally { Pop-Location }
    }
}
finally {
    & subst.exe $buildDrive /D
}
