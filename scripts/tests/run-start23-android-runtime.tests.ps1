Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$tokens = $null
$parseErrors = $null
$scriptAst = [System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $repositoryRoot 'scripts\run-start23-android.ps1'), [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -gt 0) { throw ($parseErrors -join '; ') }
$scriptAst.FindAll({
    param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -in @('Resolve-AndroidBuildMobileRoot', 'Test-AndroidMetroProcess', 'Stop-AndroidMetroProcess', 'Resolve-AndroidMetroPort', 'Invoke-AndroidAdb')
}, $true) | ForEach-Object { Invoke-Expression $_.Extent.Text }

function Test-BuildSource {
    $workspace = 'F:\workspace\mobile'
    $runtime = 'F:\ui\mobile'
    $script:nativeInputs = @{}
    foreach ($name in @('package.json', 'package-lock.json', 'app.json')) {
        $script:nativeInputs[(Join-Path $workspace $name)] = "same`r`n"
        $script:nativeInputs[(Join-Path $runtime $name)] = "same`n"
    }
    function Get-Content {
        param([string]$LiteralPath, [switch]$Raw)
        return $script:nativeInputs[$LiteralPath]
    }
    if ((Resolve-AndroidBuildMobileRoot $workspace $workspace) -ne $workspace -or
        (Resolve-AndroidBuildMobileRoot $workspace $runtime) -ne $workspace) {
        throw 'Identical native inputs, including different line endings, must reuse the workspace build.'
    }
    foreach ($name in @('package.json', 'package-lock.json', 'app.json')) {
        $script:nativeInputs[(Join-Path $runtime $name)] = 'changed'
        if ((Resolve-AndroidBuildMobileRoot $workspace $runtime) -ne $runtime) {
            throw "Different $name must build the UI source instead of refusing to launch or reusing an incompatible APK."
        }
        $script:nativeInputs[(Join-Path $runtime $name)] = "same`n"
    }
}
Test-BuildSource

$cli = 'F:\Code\mobile\node_modules\expo\bin\cli'
function Reset-Scenario {
    $script:listeners = @{}
    $script:processes = @{}
    $script:reads = @{}
    $script:stopped = [System.Collections.Generic.List[int]]::new()
    $script:recycle = $false
}
function Add-Listener {
    param([int]$OwnerId, [string]$Name = 'node.exe', [string]$Command = "node.exe `"$cli`" run:android", [int]$Port = 8081)
    $script:listeners[$Port] = @($script:listeners[$Port]) + [pscustomobject]@{ OwningProcess = $OwnerId }
    $script:listeners[$Port] = @($script:listeners[$Port] | Where-Object { $null -ne $_ })
    $script:processes[$OwnerId] = [pscustomobject]@{
        ProcessId = $OwnerId; Name = $Name; CommandLine = $Command; CreationDate = [datetime]'2026-10-06T10:00:00'
    }
}
function Get-AndroidPortListeners {
    param([int]$Port)
    if ($script:listeners.ContainsKey($Port)) { $script:listeners[$Port] }
}
function Get-AndroidServerProcess {
    param([int]$ProcessId)
    if (-not $script:processes.ContainsKey($ProcessId)) { return $null }
    if (-not $script:reads.ContainsKey($ProcessId)) { $script:reads[$ProcessId] = 0 }
    $script:reads[$ProcessId]++
    $value = $script:processes[$ProcessId].PSObject.Copy()
    if ($script:recycle -and $script:reads[$ProcessId] -gt 1) { $value.CreationDate = $value.CreationDate.AddSeconds(1) }
    return $value
}
function Stop-Process {
    param([int]$Id, [string]$ErrorAction)
    $script:stopped.Add($Id)
    foreach ($port in @($script:listeners.Keys)) {
        $script:listeners[$port] = @($script:listeners[$port] | Where-Object OwningProcess -NE $Id)
    }
}
function Start-Sleep { param([int]$Milliseconds) }
function Assert-Port {
    param([int]$Expected, [int[]]$Stopped = @())
    $actual = Resolve-AndroidMetroPort -ExpoCliPaths @($cli)
    if ($actual -ne $Expected -or ($script:stopped -join ',') -ne ($Stopped -join ',')) {
        throw "Expected port $Expected and stopped PIDs [$($Stopped -join ',')]; got $actual and [$($script:stopped -join ',')]."
    }
}

Reset-Scenario
Assert-Port 8081
Reset-Scenario
Add-Listener 100
Assert-Port 8081 @(100)
Reset-Scenario
Add-Listener 100
Add-Listener 100 # IPv4 and IPv6 listeners for the same Metro process.
Assert-Port 8081 @(100)
Reset-Scenario
Add-Listener 100 -Command 'node.exe "F:\Other\mobile\node_modules\expo\bin\cli" start'
Assert-Port 8082
Reset-Scenario
Add-Listener 100 -Name 'python.exe'
Assert-Port 8082
Reset-Scenario
Add-Listener 100 -Command "node.exe `"$cli.backup`""
Assert-Port 8082
Reset-Scenario
Add-Listener 100 -Command "node.exe `"$($cli.Replace('\', '/'))`" run:android"
Assert-Port 8081 @(100)
Reset-Scenario
Add-Listener 100
Add-Listener 200 -Command 'node.exe unrelated-server.js'
Assert-Port 8082 # Never stop one listener if another owner is unrelated.
Reset-Scenario
Add-Listener 100
$script:recycle = $true
Assert-Port 8082 # PID reuse must not terminate the replacement process.
Reset-Scenario
Add-Listener 100
$script:processes.Remove(100)
Assert-Port 8082 # Missing process metadata is insufficient proof of ownership.
Reset-Scenario
foreach ($port in 8081..8099) { Add-Listener $port -Port $port -Command 'node.exe unrelated-server.js' }
$failed = $false
try { Resolve-AndroidMetroPort -ExpoCliPaths @($cli) | Out-Null }
catch { if ($_.Exception.Message -notmatch 'No Metro port is available') { throw }; $failed = $true }
if (-not $failed -or $script:stopped.Count -ne 0) { throw 'Exhausted ports must leave unrelated services intact.' }

function Invoke-AndroidAdbProcess {
    param([string[]]$AdbArguments, [int]$TimeoutMilliseconds = 20000)
    $script:adbCalls.Add(($AdbArguments -join ' '))
    return $script:adbResults.Dequeue()
}
function Restart-AndroidAdbServer { $script:adbRecoveries++ }
$timeout = [pscustomobject]@{ TimedOut = $true; ExitCode = -1; Output = '' }
$success = [pscustomobject]@{ TimedOut = $false; ExitCode = 0; Output = "1`r`n" }
$script:adbResults = [System.Collections.Generic.Queue[object]]::new()
$script:adbCalls = [System.Collections.Generic.List[string]]::new()
$script:adbRecoveries = 0
$script:adbResults.Enqueue($success)
if ((Invoke-AndroidAdb -AdbArguments @('shell', 'getprop', 'sys.boot_completed') | Select-Object -First 1) -ne '1' -or $script:adbRecoveries -ne 0) {
    throw 'Healthy ADB command did not return its output without recovery.'
}
$script:adbResults.Enqueue($timeout)
$script:adbResults.Enqueue($success)
Invoke-AndroidAdb -AdbArguments @('devices') | Out-Null
if ($script:adbRecoveries -ne 1 -or $script:adbResults.Count -ne 0) { throw 'ADB timeout must recover and retry once.' }
$script:adbResults.Enqueue($timeout)
$script:adbResults.Enqueue($timeout)
$failed = $false
try { Invoke-AndroidAdb -AdbArguments @('devices') | Out-Null }
catch { if ($_.Exception.Message -notmatch 'ADB did not respond after automatic recovery') { throw }; $failed = $true }
if (-not $failed -or $script:adbRecoveries -ne 2) { throw 'Repeated ADB timeout must stop instead of looping forever.' }
$script:adbResults.Enqueue([pscustomobject]@{ TimedOut = $false; ExitCode = 1; Output = '' })
$failed = $false
try { Invoke-AndroidAdb -AdbArguments @('devices') | Out-Null }
catch { if ($_.Exception.Message -notmatch 'adb devices failed') { throw }; $failed = $true }
if (-not $failed -or $script:adbRecoveries -ne 2) { throw 'Normal ADB failures must not trigger daemon termination.' }
$script:adbResults.Enqueue($timeout)
$script:adbResults.Enqueue($success) # Reconnect before retrying the original command.
$script:adbResults.Enqueue($success)
Invoke-AndroidAdb -AdbArguments @('-s', 'emulator-5554', 'shell', 'df', '-k', '/data') | Out-Null
if ($script:adbRecoveries -ne 3 -or $script:adbCalls[$script:adbCalls.Count - 2] -ne '-s emulator-5554 wait-for-device') {
    throw 'Targeted ADB recovery must await the same emulator before retrying.'
}
$script:adbResults.Enqueue([pscustomobject]@{ TimedOut = $false; ExitCode = 0; Output = "Pixel_4_API_35_2`r`r`nOK`r`r`n" })
$avdName = @(Invoke-AndroidAdb -AdbArguments @('-s', 'emulator-5554', 'emu', 'avd', 'name'))
if ($avdName -notcontains 'Pixel_4_API_35_2') { throw 'Emulator console CR-CR-LF must not hide a running AVD.' }

# Exercise the daemon restart separately from the command retry above.
$scriptAst.FindAll({
    param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Restart-AndroidAdbServer'
}, $true) | ForEach-Object { Invoke-Expression $_.Extent.Text }
$adb = 'F:\Sdk\platform-tools\adb.exe'
$script:sdkServers = @(
    [pscustomobject]@{ ProcessId = 500; ExecutablePath = $adb; CreationDate = [datetime]'2026-10-06T10:00:00'; CommandLine = 'adb -L tcp:5037 fork-server server' },
    [pscustomobject]@{ ProcessId = 600; ExecutablePath = 'F:\OtherSdk\adb.exe'; CreationDate = [datetime]'2026-10-06T10:00:00'; CommandLine = 'adb -L tcp:5037 fork-server server' },
    [pscustomobject]@{ ProcessId = 700; ExecutablePath = $adb; CreationDate = [datetime]'2026-10-06T10:00:00'; CommandLine = 'adb -L tcp:5038 fork-server server' }
)
function Get-CimInstance {
    param([string]$ClassName, [string]$Filter, [string]$ErrorAction)
    if ($Filter -match '^ProcessId = (\d+)$') { return $script:sdkServers | Where-Object ProcessId -EQ ([int]$Matches[1]) }
    return $script:sdkServers
}
$daemonError = [pscustomobject]@{ TimedOut = $false; ExitCode = 1; Output = '' }
$script:stopped.Clear()
$script:adbCalls.Clear()
$script:adbResults.Enqueue($daemonError)
$script:adbResults.Enqueue($success)
Restart-AndroidAdbServer
if (($script:stopped -join ',') -ne '500' -or ($script:adbCalls -join ',') -ne 'start-server,devices') {
    throw 'Daemon recovery must spare other SDKs/ports and accept an already-recovered daemon.'
}
$script:adbCalls.Clear()
1..4 | ForEach-Object { $script:adbResults.Enqueue($daemonError) }
$failed = $false
try { Restart-AndroidAdbServer }
catch { if ($_.Exception.Message -notmatch 'Could not recover the Android SDK adb server') { throw }; $failed = $true }
if (-not $failed -or $script:adbCalls.Count -ne 4) { throw 'Unrecoverable daemon must stop after bounded attempts.' }

$taskConfig = Get-Content -LiteralPath (Join-Path $repositoryRoot '.vscode\tasks.json') -Raw | ConvertFrom-Json
$runTask = $taskConfig.tasks | Where-Object label -EQ 'Wombo: Run Android app'
if ($runTask.args -match '\$\{input:' -or $runTask.runOptions.instanceLimit -lt 2) {
    throw 'Run Android app must start without input prompts and allow restarting a running instance.'
}
if ($runTask.args[-2] -ne '-AvdName' -or $runTask.args[-1] -ne 'Pixel_4_API_35_2') {
    throw 'Run Android app must explicitly select the Pixel emulator.'
}
$avdDefault = ($scriptAst.ParamBlock.Parameters | Where-Object { $_.Name.VariablePath.UserPath -eq 'AvdName' }).DefaultValue.Value
$uiDefault = ($scriptAst.ParamBlock.Parameters | Where-Object { $_.Name.VariablePath.UserPath -eq 'UiVersion' }).DefaultValue.Value
if ($avdDefault -ne 'Pixel_4_API_35_2' -or $uiDefault -ne 'v2') {
    throw 'The direct task must select the working emulator and UI V2.'
}
Write-Host 'PASS: 5 native build source scenarios, 11 Metro lifecycle scenarios, 8 ADB scenarios and direct task startup.'
