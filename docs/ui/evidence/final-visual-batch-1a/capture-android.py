from pathlib import Path
import datetime
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

directory = Path(__file__).parent
adb = 'C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'

def command(*args):
    result = subprocess.run([adb, '-s', 'emulator-5554', *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Android verification command failed')
    return result.stdout.strip()

if sys.argv[1] == 'snapshot':
    name = sys.argv[2]
    command('shell', 'uiautomator', 'dump', '/sdcard/wombo-assets.xml')
    command('pull', '/sdcard/wombo-assets.xml', str(directory / (name + '.xml')))
    command('shell', 'screencap', '-p', '/sdcard/wombo-assets.png')
    command('pull', '/sdcard/wombo-assets.png', str(directory / (name + '.png')))
    rows = [node.attrib for node in ET.parse(directory / (name + '.xml')).iter('node')]
    print(json.dumps([{key: row.get(key) for key in ['text', 'content-desc', 'bounds', 'clickable']} for row in rows if row.get('text') or row.get('content-desc')], indent=2))
    locale = command('shell', 'getprop', 'persist.sys.locale') or command('shell', 'getprop', 'ro.product.locale')
    provenance = 'LIVE native development-only asset gallery; no athlete mutation callbacks'
    if name in ['week-after', 'acceptance-week-restored']:
        provenance = 'LIVE unchanged authenticated V2 Week, read-only navigation after gallery proof; no athlete mutation'
    record = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'serial': 'emulator-5554', 'width': command('shell', 'wm', 'size'), 'density': command('shell', 'wm', 'density'), 'fontScale': command('shell', 'settings', 'get', 'system', 'font_scale'), 'locale': locale, 'provenance': provenance}
    (directory / (name + '.json')).write_text(json.dumps(record, indent=2) + '\n')
elif sys.argv[1] == 'gallery':
    print(command('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', 'wombo:///dev-assets', 'com.adrivdbs.wombo'))
elif sys.argv[1] == 'tap':
    print(command('shell', 'input', 'tap', sys.argv[2], sys.argv[3]))
elif sys.argv[1] == 'scroll':
    print(command('shell', 'input', 'swipe', '540', '1850', '540', '650', '500'))
