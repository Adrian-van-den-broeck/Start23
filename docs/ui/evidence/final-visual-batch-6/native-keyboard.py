"""Capture the actual IME without UIAutomation suppressing its input surface."""
from pathlib import Path
import datetime, json, re, sys, time
import xml.etree.ElementTree as ET
from native_review_import import review
HERE = Path(__file__).resolve().parent
b = review.base
serial = 'emulator-5554' if '--original' in sys.argv else 'emulator-5556'
if serial == 'emulator-5554':
    import subprocess
    b.adb = lambda *args: subprocess.check_output([b.ADB, '-s', serial, *args], text=True, encoding='utf-8').strip()
for w, f in [(393, 1), (320, 2)]:
    b.dimensions(439 if w == 393 else round(1080*160/w), f)
    fixture = {'state':'availability','language':'en','width':w,'fontScale':f,'inertActions':True}
    (HERE/'fixture-config.json').write_text(json.dumps(fixture)+'\n')
    review.open_review('availability','en','keyboard-without-automation')
    for _ in range(30):
        tree = b.hierarchy()
        field = next((n for n in tree.iter('node') if n.get('class')=='android.widget.EditText'), None)
        if field is not None: break
        b.adb('shell','input','swipe','22','1820','22','700','450'); time.sleep(.6)
    else: raise AssertionError('Date input not reachable')
    box = list(map(int,re.findall(r'\d+',field.get('bounds'))))
    name = f'keyboard-{w}-font-{f}'
    ET.ElementTree(tree).write(HERE/(name+'-before-focus.xml'), encoding='utf-8')
    b.adb('shell','input','tap',str((box[0]+box[2])//2),str((box[1]+box[3])//2))
    time.sleep(20)
    ime = b.adb('shell','dumpsys','input_method')
    assert 'mInputShown=true' in ime and 'mIsInputViewShown=true' in ime
    b.adb('shell','screencap','-p','/sdcard/wombo-creation-keyboard.png')
    b.adb('pull','/sdcard/wombo-creation-keyboard.png',str(HERE/(name+'.png')))
    metadata = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'serial':serial, 'fixture':fixture,
        'provenance':'Actual focused date field and native IME screenshot; no UIAutomation after input focus',
        'nativeInputBoundsBeforeFocus':box, 'nativeKeyboardShown':True, 'nativeInputViewShown':True,
        'density':b.adb('shell','wm','density'), 'fontScale':b.adb('shell','settings','get','system','font_scale')}
    (HERE/(name+'.json')).write_text(json.dumps(metadata,indent=2)+'\n')
    # Discard the earlier post-focus automation dump paired with the suppressed IME.
    previous_xml = HERE/(name+'.xml')
    if previous_xml.exists(): previous_xml.unlink()
    if sys.argv[1:] == ['leave']: break
    b.adb('shell','input','keyevent','4'); time.sleep(1)
    print('Captured native keyboard without automation:', name, flush=True)
if serial == 'emulator-5554':
    review.open_review('availability', 'nl', 'restore-original-language')
    b.adb('shell','rm','-f','/sdcard/wombo-creation-keyboard.png')
