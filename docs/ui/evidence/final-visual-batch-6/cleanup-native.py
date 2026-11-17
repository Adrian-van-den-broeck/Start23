"""Remove only the owned review route/device/data and restore the original preview."""
from pathlib import Path
import datetime, json, shutil, subprocess, time, urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MOBILE = ROOT / '.worktrees/wombo-ui-v2-activities/mobile'
ADB = 'C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def adb(serial, *args):
    return subprocess.check_output([ADB, '-s', serial, *args], text=True, encoding='utf-8').strip()

def stop_owned_metro(pid, port):
    # Verify the specific previously observed process before stopping it.
    command = f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; if ($null -eq $p) {{ exit 0 }}; if ($p.CommandLine -notlike '*node_modules/expo/bin/cli start --dev-client --localhost --port {port}*') {{ throw 'Unexpected process owner' }}; Stop-Process -Id $p.ProcessId"
    subprocess.run(['powershell', '-NoProfile', '-Command', command], check=True, capture_output=True)

gallery = MOBILE / 'app/dev-creation-review.tsx'
assert gallery.resolve().parent == (MOBILE/'app').resolve()
assert gallery.read_bytes() == (HERE/'temporary-dev-creation-review.tsx.txt').read_bytes()
gallery.unlink()
result['galleryRemoved'] = not gallery.exists()
adb('emulator-5556', 'emu', 'kill')
for _ in range(30):
    devices = subprocess.check_output([ADB, 'devices'], text=True)
    if 'emulator-5556' not in devices: break
    time.sleep(1)
else: raise AssertionError('Owned review emulator still running')
result['temporaryEmulatorStopped'] = True
data = (ROOT/'.tmp/wombo-batch6-emulator').resolve()
assert data == ROOT.resolve()/'.tmp/wombo-batch6-emulator'
assert data.is_relative_to(ROOT.resolve()/'.tmp') and data.is_dir()
shutil.rmtree(data)
result['temporaryDataRemoved'] = not data.exists()
stop_owned_metro(35260, 8083)
result['reviewMetroStopped'] = True
adb('emulator-5554', 'reverse', '--remove', 'tcp:8083')
adb('emulator-5554', 'shell', 'rm', '-f', '/sdcard/wombo-debug-launcher.png')
adb('emulator-5554', 'shell', 'wm', 'density', '440')
adb('emulator-5554', 'shell', 'settings', 'put', 'system', 'font_scale', '1.0')
result['originalDensity'] = adb('emulator-5554', 'shell', 'wm', 'density')
result['originalFontScale'] = adb('emulator-5554', 'shell', 'settings', 'get', 'system', 'font_scale')
stop_owned_metro(17172, 8081)
metro = subprocess.Popen([shutil.which('node'), '--dns-result-order=ipv4first', 'node_modules/expo/bin/cli', 'start', '--dev-client', '--localhost', '--port', '8081'], cwd=MOBILE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
result['restoredMetroPid'] = metro.pid
for _ in range(45):
    assert metro.poll() is None, 'Restored Metro exited'
    try:
        with urllib.request.urlopen('http://127.0.0.1:8081/status', timeout=2) as response:
            if response.read().decode() == 'packager-status:running': break
    except Exception: pass
    time.sleep(1)
else: raise AssertionError('Restored preview status unavailable')
result['originalPreviewServerHealthy'] = True
adb('emulator-5554', 'reverse', 'tcp:8081', 'tcp:8081')
adb('emulator-5554', 'shell', 'am', 'force-stop', 'com.adrivdbs.wombo')
adb('emulator-5554', 'shell', "am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081' com.adrivdbs.wombo")
result['normalPreviewRequested'] = True
(HERE/'device-cleanup.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print('Owned native review cleanup complete; original preview server restored.')
