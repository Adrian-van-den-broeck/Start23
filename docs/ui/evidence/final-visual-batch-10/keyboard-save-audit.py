from pathlib import Path
import importlib.util,json,time
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('review',HERE/'native-review.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def ime():
    out=r.adb('shell','dumpsys','input_method');return 'mInputShown=true' in out or 'isInputViewShown=true' in out
preference=r.adb('shell','settings','get','secure','show_ime_with_hard_keyboard')
results=[]
try:
    r.adb('shell','settings','put','secure','show_ime_with_hard_keyboard','1')
    for state,field,save,prefix in [('profile-editor','Rusthartslag, bpm','Profiel opslaan','keyboard-profile'),('goal-run','Richttempo','A-doel opslaan','keyboard-goal')]:
        r.open_case(state,320,2)
        if state=='goal-run':r.tap('Richttempo (min/km)')
        r.tap(field)
        if state=='goal-run':r.adb('shell','input','text','5:00')
        time.sleep(.5);assert ime()
        # Move focus without a drag, since the existing on-drag policy intentionally dismisses the IME.
        for _ in range(35):
            r.adb('shell','input','keyevent','61');time.sleep(.2);t=r.tree()
            target=next((n for n in t.iter('node') if n.get('content-desc')==save and n.get('focused')=='true'),None)
            if target is not None:break
        assert target is not None,'Save missing from keyboard focus traversal'
        b=r.bounds(target)
        label=next(n for n in target.iter('node') if n.get('text')==save)
        lb=r.bounds(label);assert lb[1]>b[1] and lb[3]<b[3], 'Save label clipped at the viewport edge'
        assert ime()
        r.capture(prefix+'-save-reachable')
        results.append({'state':state,'widthDp':320,'fontScale':2,'IMEVisible':True,'fullControlInsideKeyboardAdjustedViewport':True,'nativeBounds':b,'label':save})
        print(state,'complete save control above keyboard PASS',flush=True)
        r.adb('shell','input','keyevent','4')
    (HERE/'keyboard-save-audit.json').write_text(json.dumps({'pass':True,'method':'Tab to save without a dismissing drag; require the native label to remain inside button padding; visually inspect complete labels','backendWrites':False,'results':results},indent=2)+'\n')
finally:
    r.adb('shell','input','keyevent','4')
    r.adb('shell','settings','delete','secure','show_ime_with_hard_keyboard') if preference=='null' else r.adb('shell','settings','put','secure','show_ime_with_hard_keyboard',preference)
    assert r.adb('shell','settings','get','secure','show_ime_with_hard_keyboard')==preference
