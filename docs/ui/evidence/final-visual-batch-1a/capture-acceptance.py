"""Native gallery only: observed labeled controls; no athlete callbacks."""
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

HERE = Path(__file__).parent
ADB = 'C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'


def adb(*args):
    return subprocess.check_output([ADB, '-s', 'emulator-5554', *args], text=True)


def tap(label):
    adb('shell', 'uiautomator', 'dump', '/sdcard/wombo-acceptance.xml')
    nodes = ET.fromstring(adb('shell', 'cat', '/sdcard/wombo-acceptance.xml')).iter('node')
    control = next(n for n in nodes if n.get('content-desc') == label and n.get('clickable') == 'true')
    x1, y1, x2, y2 = map(int, re.findall(r'\d+', control.get('bounds')))
    adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
    time.sleep(2)


def capture(name):
    subprocess.run(['python', str(HERE / 'capture-android.py'), 'snapshot', name], check=True, stdout=subprocess.DEVNULL)
    print('Captured ' + name, flush=True)


tap('Icons')
for page in [1, 2, 3]:
    tap(f'Icon page {page}')
    capture(f'acceptance-icons-{page}')
tap('Sports')
capture('acceptance-sports')
tap('Show UI circles')
capture('acceptance-circles')
tap('Headers')
for preview, name in [('Standard', 'standard'), ('Compact', 'compact'), ('Trees/river', 'trees-river')]:
    tap(preview)
    capture('acceptance-header-' + name)
tap('Action')
capture('acceptance-action')
try:
    adb('shell', 'wm', 'density', '540')
    time.sleep(12)
    adb('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', 'wombo:///dev-assets', 'com.adrivdbs.wombo')
    time.sleep(6)
    tap('Headers')
    tap('Standard')
    capture('acceptance-header-320')
finally:
    adb('shell', 'wm', 'density', '440')
    adb('shell', 'settings', 'put', 'system', 'font_scale', '1.0')
