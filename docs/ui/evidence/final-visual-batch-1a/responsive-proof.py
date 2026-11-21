from pathlib import Path
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from PIL import Image

directory = Path(__file__).parent
adb = 'C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'

def command(*args):
    subprocess.run([adb, '-s', 'emulator-5554', *args], check=True, capture_output=True)

def inspect():
    command('shell', 'uiautomator', 'dump', '/sdcard/wombo-responsive.xml')
    result = subprocess.check_output([adb, '-s', 'emulator-5554', 'shell', 'cat', '/sdcard/wombo-responsive.xml'])
    return list(ET.fromstring(result).iter('node'))

def open_headers():
    command('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', 'wombo:///dev-assets', 'com.adrivdbs.wombo')
    for _ in range(8):
        time.sleep(2)
        nodes = inspect()
        headers = next((n for n in nodes if n.get('content-desc') == 'Headers' and n.get('clickable') == 'true'), None)
        if headers is not None:
            x1, y1, x2, y2 = map(int, re.findall(r'\d+', headers.get('bounds')))
            command('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
            time.sleep(2)
            if any(n.get('text', '').startswith('HeaderLandscape') for n in inspect()):
                return
            continue
        # Density/font changes recreate the Android activity. An intent sent
        # before the router mounts can be lost; retry only this inert dev URL.
        command('shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', 'wombo:///dev-assets', 'com.adrivdbs.wombo')
    raise RuntimeError('Gallery did not become available; athlete data was not changed')

try:
    for width, density in [(320, 540), (360, 480), (393, 440), (412, 420)]:
        for font in [1, 2]:
            requested = f'{width}:{font}' in sys.argv[1:]
            if sys.argv[1:] and not requested:
                continue
            if (directory / f'headers-{width}-font-{font}.png').exists() and not requested:
                continue
            command('shell', 'wm', 'density', str(density))
            command('shell', 'settings', 'put', 'system', 'font_scale', str(font))
            # Reuse the live client, avoiding an extra development-client root.
            time.sleep(10)
            open_headers()
            for attempt in range(3):
                time.sleep(3)
                name = f'headers-{width}-font-{font}'
                subprocess.run(['python', str(directory / 'capture-android.py'), 'snapshot', name], check=True, stdout=subprocess.DEVNULL)
                # UI hierarchy can precede the recreated surface. Never accept
                # a blank PNG merely because a cached hierarchy has labels.
                if Image.open(directory / (name + '.png')).convert('L').crop((0, 150, 1080, 2000)).getextrema()[0] < 100:
                    break
            else:
                raise RuntimeError('Native surface stayed blank; capture is diagnostic only')
            print(f'Captured headers: {width} dp / font {font}', flush=True)
finally:
    command('shell', 'wm', 'density', '440')
    command('shell', 'settings', 'put', 'system', 'font_scale', '1.0')
