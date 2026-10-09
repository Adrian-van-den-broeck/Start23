from pathlib import Path
import importlib.util,json,time,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def focus(label):
    for _ in range(45):
        r.adb('shell','input','keyevent','61');time.sleep(.2);t=r.tree()
        if any(n.get('focused')=='true' and (n.get('content-desc')==label or n.get('text')==label) for n in t.iter('node')):return t
    raise AssertionError('Native keyboard focus missing: '+label)
def ime():
    out=r.adb('shell','dumpsys','input_method');return 'mInputShown=true' in out or 'isInputViewShown=true' in out
def field(label):
    _,b=r.target(label);r.adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(.5)
preference=r.adb('shell','settings','get','secure','show_ime_with_hard_keyboard')
results=[]
try:
    r.adb('shell','settings','put','secure','show_ime_with_hard_keyboard','1')
    assert r.adb('shell','settings','get','secure','accessibility_enabled')=='0'
    r.open_case('profile-editor');r.capture('keyboard-profile-back-focus',focus('Week'))
    r.adb('shell','input','keyevent','66');time.sleep(.5)
    assert any(n.get('content-desc')=='Fixture callback back' for n in r.tree().iter('node'))
    results.append({'tabEnterProfileBack':True,'callback':'back'})
    r.open_case('profile-editor',320,2);field('Rusthartslag, bpm');assert ime()
    r.capture('keyboard-profile-heart-rate');r.target('Profiel opslaan');assert ime();r.capture('keyboard-profile-save-reachable')
    results.append({'profileIMEVisible':True,'saveFullyVisibleAt320and200':True})
    r.adb('shell','input','keyevent','4')
    r.open_case('goal-run');r.capture('keyboard-duration-hours-focus',focus('Kies uren voor Totale richttijd'))
    r.adb('shell','input','keyevent','66');time.sleep(.6)
    assert any(n.get('content-desc')=='Duurkeuze sluiten' for n in r.tree().iter('node'))
    t=focus('Duurkeuze sluiten')
    ET.ElementTree(t).write(HERE/'keyboard-modal-close-focus.xml',encoding='utf-8')
    import subprocess
    (HERE/'keyboard-modal-close-focus.png').write_bytes(subprocess.check_output([r.ADB,'-s',r.SERIAL,'exec-out','screencap','-p'],timeout=25))
    r.adb('shell','input','keyevent','66');time.sleep(.5)
    t=r.tree();assert not any(n.get('content-desc')=='Duurkeuze sluiten' for n in t.iter('node'))
    r.capture('keyboard-duration-modal-return',t)
    focused=[n.get('content-desc') or n.get('text') for n in t.iter('node') if n.get('focused')=='true']
    results.append({'tabEnterDurationOpens':True,'tabEnterModalClose':True,'observedReturnFocus':focused})
    r.open_case('goal-run');r.capture('keyboard-goal-radio-focus',focus('Richttempo (min/km)'))
    r.adb('shell','input','keyevent','66');time.sleep(.6)
    t=r.tree();assert any(n.get('class')=='android.widget.EditText' and n.get('content-desc')=='Richttempo' for n in t.iter('node'))
    results.append({'tabEnterTargetMode':True,'paceInputAvailable':True})
    (HERE/'keyboard-review.json').write_text(json.dumps({'pass':True,'backendWrites':False,'screenReaderEnabled':False,'results':results},indent=2)+'\n')
    print('Native keyboard review PASS',flush=True)
finally:
    r.adb('shell','input','keyevent','4')
    r.adb('shell','settings','delete','secure','show_ime_with_hard_keyboard') if preference=='null' else r.adb('shell','settings','put','secure','show_ime_with_hard_keyboard',preference)
    restored=r.adb('shell','settings','get','secure','show_ime_with_hard_keyboard');assert restored==preference
    (HERE/'keyboard-cleanup.json').write_text(json.dumps({'original':preference,'restored':restored,'overrideRestored':True},indent=2)+'\n')
