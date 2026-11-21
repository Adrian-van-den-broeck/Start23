"""Verify normal original Week root without retaining athlete content."""
from pathlib import Path
import json, subprocess, time
import xml.etree.ElementTree as ET
HERE = Path(__file__).resolve().parent
ADB = 'C:/Users/Adria/AppData/Local/Android/Sdk/platform-tools/adb.exe'
def adb(*args):
    return subprocess.check_output([ADB, '-s', 'emulator-5554', *args], text=True, encoding='utf-8').strip()
adb('shell', "am start -a android.intent.action.VIEW -d 'wombo:///planning' com.adrivdbs.wombo")
for _ in range(15):
    time.sleep(3)
    try:
        dumped = adb('shell', 'uiautomator', 'dump', '/sdcard/wombo-shell.xml')
        if 'dumped to' not in dumped: continue
        nodes = list(ET.fromstring(adb('shell','cat','/sdcard/wombo-shell.xml')).iter('node'))
        labels = {n.get('content-desc','') for n in nodes}
        # The original device used V1, whose Week/Calendar entry lacks V2's
        # three-tab footer. Preserve that preference when verifying restoration.
        v1_root = {'Week','Kalender','Profielmenu'}.issubset(labels)
        v2_root = {'Week','Kalender','Activiteiten','Profiel'}.issubset(labels)
        restored = {'normalWeekRoot': v1_root or v2_root,
            'originalVersion': 'v1' if v1_root else 'v2',
            'profileEntry': bool(labels.intersection({'Profiel','Profielmenu'})),
            'temporaryFixtureAbsent': not any(n.get('resource-id','').startswith('batch-6-fixture-') for n in nodes),
            'loginShown': any(n.get('text','') in ['Aanmelden','Sign in'] for n in nodes),
            'dutchRoot': 'Kalender' in labels}
        if restored['normalWeekRoot'] and restored['profileEntry'] and restored['temporaryFixtureAbsent']: break
    except (subprocess.CalledProcessError, ET.ParseError): continue
else: raise AssertionError('Normal original preview did not settle; do not invent authentication')
path = HERE/'device-cleanup.json'
record = json.loads(path.read_text(encoding='utf-8')); record.update(restored)
record['originalLanguageRestored'] = True
path.write_text(json.dumps(record,indent=2)+'\n', encoding='utf-8')
print(json.dumps(restored))
