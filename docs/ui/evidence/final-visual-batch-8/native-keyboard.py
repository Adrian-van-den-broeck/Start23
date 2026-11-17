from pathlib import Path
import importlib.util,json,time
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review',HERE/'native-review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
assert r.adb('shell','settings','get','secure','accessibility_enabled')=='0'
r.adb('shell','wm','density','439');r.adb('shell','settings','put','system','font_scale','1');time.sleep(2)
(HERE/'fixture-config.json').write_text(json.dumps({'width':393,'fontScale':1,'language':'en','state':'before','inertActions':True})+'\n')
r.open_review('before','en');r.target('Move RUN-013 · Wisselduur')
def focus(label):
    for _ in range(30):
        r.adb('shell','input','keyevent','61');time.sleep(.3)
        tree=r.hierarchy();assert r.marker(tree,'before')
        if any(n.get('focused')=='true' and r.label_of(n)==label for n in tree.iter('node')):return tree
    raise AssertionError('Missing keyboard focus '+label)
r.capture('keyboard-entry-focus',focus('Move RUN-013 · Wisselduur'))
r.adb('shell','input','keyevent','66');time.sleep(2)
tree=r.hierarchy();assert r.marker(tree,'before') and any(n.get('resource-id')=='workout-detail-scroll' for n in tree.iter('node')),'Enter did not open the move task'
r.capture('keyboard-modal-open',tree)
r.capture('keyboard-date-focus',focus('Thursday 8 October 2026'))
r.adb('shell','input','keyevent','66');time.sleep(1)
tree=r.hierarchy()
assert any(r.label_of(n)=='Thursday 8 October 2026' and n.get('checked')=='true' for n in tree.iter('node'))
assert any(n.get('resource-id')=='batch-8-action-entry-workout-a' for n in tree.iter('node')),'Date choice must stay local'
r.capture('keyboard-date-selected',tree)
r.adb('shell','input','keyevent','4');time.sleep(2)
tree=r.hierarchy();assert not any(n.get('resource-id')=='workout-detail-scroll' for n in tree.iter('node'))
assert any(r.label_of(n)=='Move RUN-013 · Wisselduur' and n.get('focused')=='true' for n in tree.iter('node')),'Keyboard focus did not return to the exact Move entry'
assert any(n.get('resource-id')=='batch-8-action-cancel-workout-a' for n in tree.iter('node'))
r.capture('keyboard-return-focus',tree)
(HERE/'keyboard-review.json').write_text(json.dumps({'pass':True,'tabEnterDatePath':True,'dateSelectionLocal':True,'backReturnsExactMoveFocus':True,'screenReaderEnabled':False},indent=2)+'\n')
print('Native keyboard move/date/return focus passed')
