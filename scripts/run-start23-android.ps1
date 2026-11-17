param(
    [string]$AvdName = 'Pixel_4_API_35_2',
    [switch]$BuildOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$mobileRoot = Join-Path $repositoryRoot 'mobile'
$sdkRoot = $env:ANDROID_HOME
if ([string]::IsNullOrWhiteSpace($sdkRoot)) {
    $sdkRoot = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
}
$adb = Join-Path $sdkRoot 'platform-tools\adb.exe'
$emulator = Join-Path $sdkRoot 'emulator\emulator.exe'
$expo = Join-Path $mobileRoot 'node_modules\expo\bin\cli'
foreach ($tool in @($adb, $emulator, $expo)) {
    if (-not (Test-Path -LiteralPath $tool)) {
        throw "Missing '$tool'. Install the Android SDK and run npm ci in mobile first."
    }
}
$env:ANDROID_HOME = $sdkRoot
$env:ANDROID_SDK_ROOT = $sdkRoot
$env:ANDROID_USER_HOME = Join-Path $env:USERPROFILE '.android'
$env:NODE_ENV = 'development'

function Invoke-AndroidAdb {
    param([string[]]$AdbArguments)
    $output = & $adb @AdbArguments
    if ($LASTEXITCODE -ne 0) {
        throw "adb $($AdbArguments -join ' ') failed."
    }
    return $output
}

$architecture = 'x86_64'
$serial = $null
if (-not $BuildOnly) {
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
    foreach ($port in @(8081, 8000)) {
        Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'reverse', "tcp:$port", "tcp:$port") | Out-Null
    }
}

# SUBST exposes this checkout under a short path without copying or moving it.
# Use a free drive and release only the mapping created by this invocation.
$buildDrive = $null
foreach ($letter in 90..68) {
    $candidateDrive = "$([char]$letter):"
    if (-not (Test-Path "$candidateDrive\") -and
        $null -eq (Get-PSDrive -Name ([string][char]$letter) -ErrorAction SilentlyContinue)) {
        & subst.exe $candidateDrive $repositoryRoot
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
            --init-script "$buildDrive\scripts\android-short-paths.gradle" `
            "-Dstart23.nativeRoot=$buildDrive/.runtime/android-native" `
            '-PreactNativeDevServerPort=8081' "-PreactNativeArchitectures=$architecture"
        if ($LASTEXITCODE -ne 0) { throw 'Android development build failed; see the Gradle output above.' }
    }
    finally { Pop-Location }

    $apk = Join-Path $mobileRoot 'android\app\build\outputs\apk\debug\app-debug.apk'
    if (-not (Test-Path -LiteralPath $apk)) { throw "Gradle did not produce '$apk'." }
    if ($BuildOnly) {
        Write-Host "[Wombo] Development APK built: $apk"
    }
    else {
        Write-Host "[Wombo] Installing development app on $serial..."
        $deviceName = @(Invoke-AndroidAdb -AdbArguments @('-s', $serial, 'emu', 'avd', 'name'))[0].Trim()
        Push-Location $mobileRoot
        try {
            $env:REACT_NATIVE_PACKAGER_HOSTNAME = '127.0.0.1'
            Write-Host '[Wombo] Starting Metro and opening the app on localhost:8081...'
            & node $expo run:android --binary $apk --device $deviceName --port 8081 --no-install
            if ($LASTEXITCODE -ne 0) { throw 'Expo failed to start the Android app.' }
        }
        finally { Pop-Location }
    }
}
finally {
    & subst.exe $buildDrive /D
}
