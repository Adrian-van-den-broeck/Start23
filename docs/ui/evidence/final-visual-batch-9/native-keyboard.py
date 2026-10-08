from pathlib import Path
import importlib.util,json,time
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
results=[]
def begin(state):
    r.adb('shell','wm','density','439');r.adb('shell','settings','put','system','font_scale','1');time.sleep(1)
    (HERE/'fixture-config.json').write_text(json.dumps({'width':393,'fontScale':1,'language':'en','state':state,'build':'final-4','inertActions':True})+'\n')
    r.open_review(state,'en')
def focus(predicate,state):
    for _ in range(50):
        r.adb('shell','input','keyevent','61');time.sleep(.3)
        tree=r.hierarchy();assert r.marker(tree,state)
        if any(n.get('focused')=='true' and predicate(r.label_of(n)) for n in tree.iter('node')):return tree
    raise AssertionError('Expected native keyboard focus was not observed')
def check_action(value):
    tree=r.hierarchy();assert any(n.get('resource-id')=='batch-9-action-'+value for n in tree.iter('node')),value
    return tree
def ime():
    out=r.adb('shell','dumpsys','input_method')
    return 'mInputShown=true' in out or 'isInputViewShown=true' in out
preference=r.adb('shell','settings','get','secure','show_ime_with_hard_keyboard')
try:
    r.adb('shell','settings','put','secure','show_ime_with_hard_keyboard','1')
    assert r.adb('shell','settings','get','secure','accessibility_enabled')=='0'
    begin('rpe')
    r.capture('keyboard-rpe-focus',focus(lambda s:s.startswith('Save RPE · ') and s.endswith('(RPE 4)'),'rpe'))
    r.adb('shell','input','keyevent','66');time.sleep(1)
    tree=check_action('rpe-activity-a-4-hr-');assert any(n.get('resource-id')=='v2-activities' for n in tree.iter('node'))
    r.capture('keyboard-immediate-feedback-return',tree);results.append({'tabEnterImmediateRpe':True,'noSaveStep':True,'exactActivity':'activity-a','canonicalValue':4})
    begin('entry');r.tap('Distance (metres, optional)');time.sleep(1)
    assert ime(),'Entry keyboard did not become visible'
    r.capture('keyboard-entry-distance')
    _,box=r.target('Save activity');assert ime(),'Keyboard must remain visible while final Save is reached'
    r.capture('keyboard-entry-save-reachable');results.append({'entryKeyboardVisible':True,'saveFullyWithinScrollViewport':True,'saved':False})
    r.adb('shell','input','keyevent','4');time.sleep(.5)
    begin('rpeHR');r.tap('Average heart rate (bpm)');time.sleep(1);assert ime()
    r.capture('keyboard-feedback-heart-rate')
    # Scrolling keeps the IME open and exposes the original immediate-save choice.
    for _ in range(20):
        tree=r.hierarchy();labels=[r.label_of(n) for n in tree.iter('node') if r.label_of(n).startswith('Save RPE · ') and r.label_of(n).endswith('(RPE 4)')]
        if labels:break
        r.scroll(tree)
    else:raise AssertionError('RPE 4 missing above keyboard')
    r.target(labels[0]);assert ime();r.capture('keyboard-feedback-choice-reachable')
    results.append({'feedbackKeyboardVisible':True,'canonicalChoiceFullyWithinScrollViewport':True,'saved':False})
    r.adb('shell','input','keyevent','4');time.sleep(.5)
    (HERE/'keyboard-review.json').write_text(json.dumps({'pass':True,'screenReaderEnabled':False,'backendWrites':False,'results':results},indent=2)+'\n')
    print('Native Tab/Enter immediate RPE and IME reachable entry/feedback passed')

finally:
    r.adb('shell','settings','delete','secure','show_ime_with_hard_keyboard') if preference=='null' else r.adb('shell','settings','put','secure','show_ime_with_hard_keyboard',preference)
    restored=r.adb('shell','settings','get','secure','show_ime_with_hard_keyboard');assert restored==preference
    (HERE/'keyboard-cleanup.json').write_text(json.dumps({'softKeyboardReviewOverrideRestored':True,'original':preference,'restored':restored},indent=2)+'\n')
