"""Actual Android AvailabilityScreen/SelectionScreen and accepted shell components; public inert fixtures."""
from pathlib import Path
import datetime, importlib.util, json, re, sys, time
import xml.etree.ElementTree as ET
import subprocess
from PIL import Image
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('shell_review', HERE.parent/'final-visual-batch-2/native-review.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.HERE = HERE
def isolated_adb(*args):
    return subprocess.check_output([base.ADB, '-s', 'emulator-5556', *args], text=True, encoding='utf-8', errors='strict').strip()
base.adb = isolated_adb
_raw_hierarchy = base.hierarchy
def settled_hierarchy():
    # Density/deep-link transitions can momentarily return no accessibility root.
    # Retry the actual dump; never reuse stale XML or a non-fixture screenshot.
    for attempt in range(8):
        try: return _raw_hierarchy()
        except (RuntimeError, subprocess.CalledProcessError):
            if attempt == 7: raise
            time.sleep(1)
base.hierarchy = settled_hierarchy

def capture(name, tree=None, modal=False):
    tree = tree if tree is not None else base.hierarchy()
    expected_state = json.loads((HERE/'fixture-config.json').read_text())['state']
    marker = any(n.get('resource-id') == 'batch-6-fixture-'+expected_state for n in tree.iter('node'))
    assert marker, 'Refuse non-fixture capture: '+name
    ET.ElementTree(tree).write(HERE/(name+'.xml'), encoding='utf-8')
    base.adb('shell', 'screencap', '-p', '/sdcard/wombo-creation.png')
    base.adb('pull', '/sdcard/wombo-creation.png', str(HERE/(name+'.png')))
    # A development refresh overlay is transient evidence, not accepted UI.
    for attempt in range(5):
        im = Image.open(HERE/(name+'.png')).convert('RGB').crop((0, 0, 1080, 600))
        blue = sum(1 for r,g,b in im.getdata() if b > 150 and b > r*1.6 and g > r*1.6)
        if blue < 10000: break
        time.sleep(4)
        tree = base.hierarchy()
        assert any(n.get('resource-id') == 'batch-6-fixture-'+expected_state for n in tree.iter('node')), 'Lost fixture during refresh'
        ET.ElementTree(tree).write(HERE/(name+'.xml'), encoding='utf-8')
        base.adb('shell', 'screencap', '-p', '/sdcard/wombo-creation.png')
        base.adb('pull', '/sdcard/wombo-creation.png', str(HERE/(name+'.png')))
    else: raise AssertionError('Unsettled development overlay: '+name)
    record = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'serial': 'emulator-5556',
        'size': base.adb('shell', 'wm', 'size'), 'density': base.adb('shell', 'wm', 'density'),
        'fontScale': base.adb('shell', 'settings', 'get', 'system', 'font_scale'),
        'fixture': json.loads((HERE/'fixture-config.json').read_text()),
        'provenance': 'Actual AvailabilityScreen and SelectionScreen with public occurrence DTO variants; exact production mapper and primitives; inert mutation ledger; no backend or athlete writes'}
    (HERE/(name+'.json')).write_text(json.dumps(record, indent=2)+'\n')
    print('Captured '+name, flush=True)

def open_review(state, language='nl', review='initial'):
    path = f'dev-creation-review?state={state}&language={language}&review={review}-{time.time_ns()}'
    base.open_path(path)
    for attempt in range(20):
        tree = base.hierarchy()
        nodes = list(tree.iter('node'))
        title = any((n.get('text') or n.get('content-desc')) in ['Wanneer kun je trainen?', 'When can you train?', 'Kies je trainingen', 'Choose your workouts'] for n in nodes)
        marker = any(n.get('resource-id') == 'batch-6-fixture-'+state for n in nodes)
        back = any(n.get('content-desc') == ('Terug naar Week' if language == 'nl' else 'Back to Week') for n in nodes)
        if title and marker and back: return
        if attempt % 4 == 3: base.open_path(path)
        time.sleep(1)
    raise AssertionError('Creation fixture did not settle')

def pages(prefix):
    seen = set()
    for part in range(96):
        tree = base.hierarchy()
        signature = tuple((n.get('text'), n.get('content-desc'), n.get('bounds')) for n in tree.iter('node'))
        if signature in seen: return
        seen.add(signature)
        capture(prefix+f'-page-{part}', tree)
        nodes = list(tree.iter('node'))
        boxes = [list(map(int, re.findall(r'\d+', n.get('bounds')))) for n in nodes if n.get('class') == 'android.widget.ScrollView' and n.get('scrollable') == 'true']
        if not boxes: return
        # Use overlapping viewports so an enlarged control clipped on one edge
        # is completely visible in the next capture, not skipped by a long swipe.
        box = min(boxes, key=lambda b: b[3]-b[1])
        x = box[0]+max(12, (box[2]-box[0])//50)
        base.adb('shell', 'input', 'swipe', str(x), str(round(box[1]+(box[3]-box[1])*.8)), str(x), str(round(box[1]+(box[3]-box[1])*.3)), '450')
        time.sleep(1)
    raise AssertionError('Unexpected scroll loop')

def run_case(width, font, language, state):
    # Physical display is 1080 pixels. The closest integer density is recorded.
    # Match accepted Batch 3's ~393 dp setup: 440 dpi gives 392.73 dp,
    # just below the 393 dp focus-padding threshold; 439 gives 393.62 dp.
    density = 439 if width == 393 else round(1080 * 160 / width)
    base.dimensions(density, font)
    (HERE/'fixture-config.json').write_text(json.dumps({'language': language, 'state': state, 'width': width, 'fontScale': font, 'inertActions': True})+'\n')
    prefix = f'{width}-font-{font}-{language}-{state}'
    for path in HERE.glob(prefix+'-page-*'):
        if path.suffix in ['.png', '.xml', '.json']:
            assert path.resolve().parent == HERE
            path.unlink()
    open_review(state, language, prefix)
    pages(prefix)

if __name__ == '__main__':
    if sys.argv[1] == 'load':
        (HERE/'fixture-config.json').write_text(json.dumps({'language':'nl','state':'selection','inertActions':True})+'\n')
        base.adb('reverse', 'tcp:8083', 'tcp:8083')
        base.adb('shell', 'am', 'force-stop', 'com.adrivdbs.wombo')
        base.adb('shell', "am start -a android.intent.action.VIEW -d 'wombo://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8083' com.adrivdbs.wombo")
        time.sleep(15)
        run_case(393, 1, 'nl', 'selection')
    elif sys.argv[1] == 'case': run_case(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5])
    elif sys.argv[1] == 'capture': capture(sys.argv[2])
